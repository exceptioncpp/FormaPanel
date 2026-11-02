"""Candidate-only safety boundaries; optional executable weather template fixtures."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
import ast

import yaml

try:
    from jinja2 import Environment
except ImportError:
    Environment = None

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = yaml.safe_load((ROOT / "config/ha/packages/formapanel-living.yaml").read_text(encoding="utf-8"))
SENSORS = {s["default_entity_id"]: s for block in PACKAGE["template"] for s in block.get("sensor", [])}
PREFIX = "formapanel_living_"


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class VirtualContractTests(unittest.TestCase):
    def test_no_physical_write_or_hidden_transport(self):
        self.assertEqual(set(PACKAGE), {"input_select", "input_number", "input_boolean", "script", "template"})
        actions = [x for x in walk(PACKAGE) if "action" in x or "service" in x]
        self.assertEqual({x["action"] for x in actions}, {"input_boolean.turn_on", "input_boolean.turn_off"})
        self.assertTrue(all(x["target"] == {"entity_id": "input_boolean.formapanel_living_primary_light_requested"} for x in actions))
        text = yaml.safe_dump(PACKAGE)
        for forbidden in ("rest_command", "shell_command", "python_script", "mqtt.publish", "home_living_", "bedroom", "office", "climate.set", "light.turn"):
            self.assertNotIn(forbidden, text)
        for domain in ("input_select", "input_number", "input_boolean", "script"):
            self.assertTrue(all(key.startswith(PREFIX) for key in PACKAGE[domain]))

    def test_desire_never_implies_actual_or_readiness(self):
        ready = PACKAGE["template"][0]["binary_sensor"][0]
        self.assertEqual(ready["state"], "{{ false }}")
        for slot in ("primary_light_actual", "heating_actual", "cooling_actual"):
            self.assertEqual(SENSORS["sensor." + PREFIX + slot]["state"], "unknown")
        self.assertEqual(SENSORS["sensor." + PREFIX + "backend_status"]["state"], "unbound")
        self.assertFalse(PACKAGE["input_boolean"][PREFIX + "backend_connected"]["initial"])

    def test_helpers_restore_and_target_contract(self):
        for domain in ("input_select", "input_number", "input_boolean"):
            for key, value in PACKAGE[domain].items():
                if key not in (PREFIX + "backend_connected", PREFIX + "weather_max_age_seconds"):
                    self.assertNotIn("initial", value)
        self.assertEqual(PACKAGE["input_select"][PREFIX + "mode"]["options"], ["Auto", "Manual"])
        target = PACKAGE["input_number"][PREFIX + "target"]
        self.assertEqual((target["min"], target["max"], target["step"]), (16, 28, 0.1))
        self.assertEqual(PACKAGE["script"][PREFIX + "light_toggle"]["mode"], "queued")
        self.assertEqual(PACKAGE["input_number"][PREFIX + "weather_max_age_seconds"]["initial"], 7200)
        self.assertEqual(SENSORS["sensor." + PREFIX + "heartbeat"]["state"], "{{ as_timestamp(now()) | int }}")

    def test_forecast_is_attributes_not_oversize_state(self):
        forecast = SENSORS["sensor." + PREFIX + "weather_tomorrow"]
        self.assertIn("entries", forecast["attributes"])
        self.assertNotIn("to_json", forecast["state"])
        self.assertLess(len(forecast["state"]), 255)
        self.assertEqual(len(SENSORS), len({s["unique_id"] for s in SENSORS.values()}))

    def test_five_day_contract_has_numeric_states_and_nullable_attributes(self):
        days = SENSORS["sensor." + PREFIX + "weather_forecast_days"]
        self.assertIn("days", days["attributes"])
        self.assertLess(len(days["state"]), 255)
        for index in range(5):
            slot = SENSORS["sensor." + PREFIX + f"weather_day_{index}"]
            self.assertEqual(slot["unit_of_measurement"], "°C")
            self.assertIn("availability", slot)
            self.assertTrue({"low", "condition", "date", "source_entity", "updated_at", "periods"} <= slot["attributes"].keys())
            self.assertNotIn("to_json", slot["state"])


@unittest.skipUnless(Environment, "Jinja2 unavailable locally; no dependency installation or network access")
class WeatherTemplateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 1, 11, 20, tzinfo=timezone(timedelta(hours=3)))
        self.values = {"input_number.formapanel_living_weather_max_age_seconds": "3600"}
        self.attrs = {}
        self.updated = {}

    def provider(self, entity, *, age=60, state="cloudy", rows=None, unit="°C"):
        self.values[entity] = state
        self.attrs[entity] = {"temperature": 6, "temperature_unit": unit, "forecast_twice_daily": rows}
        self.updated[entity] = self.now - timedelta(seconds=age)

    def render(self, name, field="state"):
        test = self

        class States:
            def __call__(self, entity):
                return test.values.get(entity, "unknown")

            def __getitem__(self, entity):
                return SimpleNamespace(last_updated=test.updated.get(entity, test.now))

        def as_datetime(value, default=None):
            try:
                return datetime.fromisoformat(value) if isinstance(value, str) else value if isinstance(value, datetime) else default
            except (ValueError, TypeError):
                return default

        def as_timestamp(value, default=0):
            value = as_datetime(value)
            return value.timestamp() if value is not None else default

        env = Environment()
        env.globals.update(states=States(), state_attr=lambda e, a: self.attrs.get(e, {}).get(a),
                           has_value=lambda e: self.values.get(e, "unknown") not in ("unknown", "unavailable"),
                           is_number=lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
                           now=lambda: self.now, timedelta=timedelta, as_datetime=as_datetime,
                           as_timestamp=as_timestamp, as_local=lambda d: d.astimezone(self.now.tzinfo))
        definition = SENSORS["sensor." + PREFIX + name]
        template = definition[field] if field in ("state", "availability") else definition["attributes"][field]
        return env.from_string(template).render().strip()

    @staticmethod
    def row(**changes):
        return {"datetime": "2026-11-02T12:00:00+03:00", "native_temperature": 7,
                "native_templow": 5, "condition": "rainy", "is_daytime": True, **changes}

    def test_primary_current_and_unconfigured_ttl(self):
        self.provider("weather.yandex_pogoda")
        self.provider("weather.home_assistant_gismeteo")
        self.assertEqual(self.render("weather_source"), "weather.yandex_pogoda")
        self.values["input_number.formapanel_living_weather_max_age_seconds"] = "0"
        self.assertEqual(self.render("weather_source"), "unavailable")

    def test_expired_unavailable_future_or_wrong_units_fall_back(self):
        for args in ({"age": 4000}, {"state": "unavailable"}, {"age": -60}, {"unit": "°F"}):
            with self.subTest(args=args):
                self.provider("weather.yandex_pogoda", **args)
                self.provider("weather.home_assistant_gismeteo")
                self.assertEqual(self.render("weather_source"), "weather.home_assistant_gismeteo")

    def test_missing_malformed_or_wrong_day_forecast_has_no_fake_zero(self):
        for rows in (None, [], "bad", [None, 4], [self.row(datetime="bad")],
                     [self.row(datetime="2026-11-01T12:00:00+03:00")], [self.row(native_temperature=None)]):
            with self.subTest(rows=rows):
                self.provider("weather.yandex_pogoda", rows=rows)
                self.assertEqual(self.render("weather_forecast_source"), "unavailable")

    def test_forecast_fallback_is_independent_and_partial_rows_survive(self):
        self.provider("weather.yandex_pogoda", rows=[])
        self.provider("weather.home_assistant_gismeteo", rows=[self.row(), self.row(datetime="bad")])
        self.assertEqual(self.render("weather_source"), "weather.yandex_pogoda")
        self.assertEqual(self.render("weather_forecast_source"), "weather.home_assistant_gismeteo")
        self.values["sensor.formapanel_living_weather_forecast_source"] = "weather.home_assistant_gismeteo"
        rows = ast.literal_eval(self.render("weather_tomorrow", "entries"))
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["high"], rows[0]["low"]), (7, 5))

    def test_missing_low_keeps_forecast_and_low_unavailable(self):
        self.provider("weather.yandex_pogoda", rows=[self.row(native_templow=None)])
        self.assertEqual(self.render("weather_forecast_source"), "weather.yandex_pogoda")
        self.values["sensor.formapanel_living_weather_forecast_source"] = "weather.yandex_pogoda"
        rows = ast.literal_eval(self.render("weather_tomorrow", "entries"))
        self.assertIsNone(rows[0]["low"])
        self.attrs["sensor.formapanel_living_weather_tomorrow"] = {"entries": rows}
        self.assertEqual(self.render("weather_tomorrow_high"), "7.0")
        self.assertEqual(self.render("weather_tomorrow_low", "availability"), "False")
        compact = ast.literal_eval(self.render("weather_tomorrow", "rows"))
        self.assertEqual(set(compact[0]), {"date", "condition", "high", "low"})
        self.assertEqual(compact[0]["date"], "2026-11-02")

    def test_wind_normalizes_units_and_rejects_unknown_unit(self):
        self.values["sensor.formapanel_living_weather_source"] = "weather.yandex_pogoda"
        self.provider("weather.yandex_pogoda")
        for unit, expected in [("m/s", 36), ("km/h", 10), ("mph", 16.09), ("kn", 18.52)]:
            self.attrs["weather.yandex_pogoda"].update(wind_speed=10, wind_speed_unit=unit)
            self.assertEqual(self.render("weather_wind_speed", "availability"), "True")
            self.assertAlmostEqual(float(self.render("weather_wind_speed")), expected)
        self.attrs["weather.yandex_pogoda"]["wind_speed_unit"] = "bad-unit"
        self.assertEqual(self.render("weather_wind_speed", "availability"), "False")
        self.assertEqual(self.render("weather_wind_speed"), "None")

    def test_pressure_units_explicit_and_unknown_missing_unavailable(self):
        self.values["sensor.formapanel_living_weather_source"] = "weather.yandex_pogoda"
        self.provider("weather.yandex_pogoda")
        self.attrs["weather.yandex_pogoda"].update(pressure=760, pressure_unit="mmHg")
        self.assertEqual(self.render("weather_pressure", "availability"), "True")
        self.assertAlmostEqual(float(self.render("weather_pressure")), 1013.25, places=2)
        self.attrs["weather.yandex_pogoda"]["pressure"] = None
        self.assertEqual(self.render("weather_pressure", "availability"), "False")

    def test_all_offline_and_recovery_reselect_primary(self):
        self.provider("weather.yandex_pogoda", state="unavailable", rows=[self.row()])
        self.provider("weather.home_assistant_gismeteo", state="unavailable", rows=[self.row()])
        self.assertEqual(self.render("weather_source"), "unavailable")
        self.assertEqual(self.render("weather_forecast_source"), "unavailable")
        self.provider("weather.home_assistant_gismeteo", rows=[self.row()])
        self.assertEqual(self.render("weather_source"), "weather.home_assistant_gismeteo")
        self.provider("weather.yandex_pogoda", rows=[self.row()])
        self.assertEqual(self.render("weather_source"), "weather.yandex_pogoda")
        self.assertEqual(self.render("weather_forecast_source"), "weather.yandex_pogoda")

    def test_heartbeat_advances_without_commands_and_unknowns_remain_unknown(self):
        first = int(self.render("heartbeat"))
        self.now += timedelta(minutes=1)
        self.assertEqual(int(self.render("heartbeat")) - first, 60)
        for slot in ("primary_light_actual", "heating_actual", "cooling_actual"):
            self.assertEqual(self.render(slot), "unknown")

    def test_light_actual_is_baseline_when_desired_diverges(self):
        template = PACKAGE["script"][PREFIX + "light_toggle"]["sequence"][0]["variables"]["baseline"]
        for actual, requested, baseline in [("on", "off", "on"), ("off", "on", "off"),
                                             ("unknown", "on", "on"), ("unavailable", "off", "off"),
                                             ("unknown", "unknown", "unknown")]:
            values = {"sensor.formapanel_living_primary_light_actual": actual,
                      "input_boolean.formapanel_living_primary_light_requested": requested}
            rendered = Environment().from_string(template).render(states=lambda e: values[e]).strip()
            self.assertEqual(rendered, baseline)
        # An unknown baseline fails the script condition; no helper mutation is sent.
        condition = PACKAGE["script"][PREFIX + "light_toggle"]["sequence"][1]["value_template"]
        self.assertEqual(Environment().from_string(condition).render(baseline="unknown"), "False")

    def test_datetime_compared_in_home_timezone(self):
        self.provider("weather.yandex_pogoda", rows=[self.row(datetime="2026-11-01T22:00:00+00:00")])
        self.assertEqual(self.render("weather_forecast_source"), "weather.yandex_pogoda")

    def test_five_days_aggregate_periods_sort_and_exclude_outside_horizon(self):
        rows = [self.row(datetime=f"2026-11-{day:02d}T12:00:00+03:00", native_temperature=day,
                         native_templow=None if day == 4 else day - 2)
                for day in (7, 6, 5, 4, 3, 2, 1)]
        rows += [self.row(native_temperature=9, native_templow=0, condition="cloudy", is_daytime=False),
                 self.row(datetime="bad"), None]
        self.provider("weather.yandex_pogoda", rows=rows)
        self.values["sensor.formapanel_living_weather_forecast_source"] = "weather.yandex_pogoda"
        days = ast.literal_eval(self.render("weather_forecast_days", "days"))
        self.assertEqual([day["date"] for day in days], [f"2026-11-{day:02d}" for day in range(2, 7)])
        self.assertEqual((days[0]["high"], days[0]["low"], days[0]["condition"], days[0]["periods"]),
                         (9, 0, "rainy", 2))
        self.assertIsNone(days[2]["low"])
        self.attrs["sensor.formapanel_living_weather_forecast_days"] = {"days": days}
        for index, day in enumerate(days):
            self.assertEqual(self.render(f"weather_day_{index}", "availability"), "True")
            self.assertEqual(float(self.render(f"weather_day_{index}")), day["high"])
            self.assertEqual(self.render(f"weather_day_{index}", "date"), day["date"])
        self.assertEqual(self.render("weather_day_2", "low"), "None")

    def test_five_days_never_blend_sources_or_fill_missing_days(self):
        self.provider("weather.yandex_pogoda", rows=[self.row()])
        self.provider("weather.home_assistant_gismeteo", rows=[
            self.row(datetime=f"2026-11-{day:02d}T12:00:00+03:00", native_temperature=99)
            for day in range(2, 7)])
        selected = self.render("weather_forecast_source")
        self.assertEqual(selected, "weather.yandex_pogoda")
        self.values["sensor.formapanel_living_weather_forecast_source"] = selected
        days = ast.literal_eval(self.render("weather_forecast_days", "days"))
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0]["high"], 7)
        self.attrs["sensor.formapanel_living_weather_forecast_days"] = {"days": days}
        self.assertEqual(self.render("weather_day_0", "availability"), "True")
        for index in range(1, 5):
            self.assertEqual(self.render(f"weather_day_{index}", "availability"), "False")
            self.assertEqual(self.render(f"weather_day_{index}"), "None")
            self.assertEqual(self.render(f"weather_day_{index}", "low"), "None")

    def test_five_days_fallback_then_expiry_clears_all_slots(self):
        self.provider("weather.yandex_pogoda", rows=[], age=4000)
        self.provider("weather.home_assistant_gismeteo", rows=[self.row()])
        self.values["sensor.formapanel_living_weather_forecast_source"] = self.render("weather_forecast_source")
        self.assertEqual(self.values["sensor.formapanel_living_weather_forecast_source"], "weather.home_assistant_gismeteo")
        self.assertEqual(len(ast.literal_eval(self.render("weather_forecast_days", "days"))), 1)
        self.provider("weather.home_assistant_gismeteo", rows=[self.row()], age=4000)
        self.values["sensor.formapanel_living_weather_forecast_source"] = self.render("weather_forecast_source")
        days = ast.literal_eval(self.render("weather_forecast_days", "days"))
        self.assertEqual(days, [])
        self.attrs["sensor.formapanel_living_weather_forecast_days"] = {"days": days}
        for index in range(5):
            self.assertEqual(self.render(f"weather_day_{index}", "availability"), "False")


if __name__ == "__main__":
    unittest.main()
