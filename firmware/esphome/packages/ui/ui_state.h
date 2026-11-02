#pragma once
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <string>
#include <algorithm>

namespace formapanel {
enum class Command { IDLE, PENDING, CONFIRMED, ACCEPTED_UNBOUND, TIMEOUT, UNAVAILABLE, ERROR };
struct Day {
  std::string title{"--"}, condition;
  float high{NAN}, low{NAN};
};
struct State {
  bool connected{false}, helpers_ready{false}, contract_ready{false}, mock{false};
  bool light_known{false}, light_on{false}, light_expected{false};
  bool light_requested_known{false}, light_requested{false};
  bool mode_known{false}, target_known{false}, heat_known{false}, cool_known{false};
  bool manual_heat{false}, manual_cool{false};
  int mode{0}, requested_mode{0};
  float target{NAN}, requested_target{NAN}, temperature{NAN}, humidity{NAN}, co2{NAN};
  float outdoor{NAN}, wind{NAN}, weather_humidity{NAN}, pressure{NAN};
  std::string condition_code;
  Day forecast_days[5];
  float panel_brightness{100}, light_brightness{NAN};
  bool light_brightness_known{false};
  float brightness_expected{NAN};
  Command brightness_command{Command::IDLE};
  uint32_t brightness_started{0};
  unsigned brightness_sent{0};
  std::string backend_status{"unbound"};
  bool begin_brightness(float value,uint32_t now) {
    if(brightness_command==Command::PENDING) return false;
    if(!connected || !contract_ready || !light_brightness_known) { brightness_command=Command::UNAVAILABLE; return false; }
    if(!std::isfinite(value) || value<0 || value>100) { brightness_command=Command::ERROR; return false; }
    value=std::round(value);
    if(std::fabs(value-light_brightness)<0.5f) return false;
    brightness_expected=value; brightness_started=now;
    brightness_command=Command::PENDING; ++brightness_sent; return true;
  }
  void brightness_feedback(float value) {
    light_brightness_known=std::isfinite(value) && value>=0 && value<=100;
    light_brightness=light_brightness_known ? value:NAN;
    if(!light_brightness_known) {
      if(brightness_command==Command::PENDING) brightness_command=Command::UNAVAILABLE;
    } else if(brightness_command==Command::PENDING && std::fabs(value-brightness_expected)<0.5f)
      brightness_command=Command::CONFIRMED;
  }
  void brightness_error(unsigned request_id) {
    if(brightness_command==Command::PENDING && request_id==brightness_sent)
      brightness_command=Command::ERROR;
  }
  std::string brightness_detail() const {
    if(!connected) return "Нет связи с HA";
    if(brightness_command==Command::PENDING) return "Яркость: ожидаем подтверждение HA";
    if(brightness_command==Command::TIMEOUT) return "Яркость: нет подтверждения HA";
    if(brightness_command==Command::ERROR) return "Яркость: ошибка запроса HA";
    if(!light_brightness_known) return "Яркость не получена из HA";
    return mock ? "Демонстрация / устройства не подключены" : "Запрошенная яркость / устройство не подключено";
  }
  bool arc_editing{false}, light_editing{false}, brightness_editing{false};
  float tomorrow_high{NAN}, tomorrow_low{NAN};
  std::string tomorrow_condition{""}, forecast_source{""};
  bool climate_pending{false};
  int climate_kind{-1};
  float climate_expected{NAN};
  uint32_t climate_started{0};
  std::string climate_error{""};
  void climate_begin(int kind,float expected,uint32_t now) {
    climate_kind=kind;climate_expected=expected;climate_started=now;
    climate_pending=true;climate_error.clear();
  }
  void climate_feedback(int kind,float value) {
    if(climate_pending && climate_kind==kind && std::isfinite(value) && std::fabs(value-climate_expected)<0.051f)
      climate_pending=false;
  }
  std::string clock{"--:--"}, forecast{"Прогноз недоступен"}, weather_source{"Нет данных"};
  std::string condition{"Нет данных"}, heating_actual{"Не подключено"}, cooling_actual{"Не подключено"};
  Command light_command{Command::IDLE};
  uint32_t light_started{0};
  unsigned light_sent{0};
  bool turbo_running{false};
  uint32_t turbo_started{0}, turbo_duration{600000};
  bool begin_light(uint32_t now) {
    if (!connected || !contract_ready || !light_requested_known) { light_command=Command::UNAVAILABLE; return false; }
    if (light_command==Command::PENDING) return false;
    light_expected=!(light_known ? light_on : light_requested); light_started=now;
    light_command=Command::PENDING; ++light_sent; return true;
  }
  void request_feedback(bool known,bool on) {
    light_requested_known=known; light_requested=on;
    if(known && !light_known && light_command==Command::PENDING && on==light_expected)
      light_command=Command::ACCEPTED_UNBOUND;
  }
  void light_feedback(bool known, bool on) {
    light_known=known;
    if (known) {
      light_on=on;
      if (light_command==Command::PENDING && on==light_expected) light_command=Command::CONFIRMED;
    }
  }
  void disconnect() {
    connected=false; helpers_ready=false; contract_ready=false; light_known=false; light_requested_known=false;
    climate_pending=false; climate_error="Нет связи с HA";
    mode_known=target_known=heat_known=cool_known=false;
    temperature=humidity=co2=outdoor=wind=weather_humidity=pressure=tomorrow_high=tomorrow_low=NAN; clock="--:--";
    condition_code.clear(); forecast_source.clear();
    for(auto &day:forecast_days) day=Day{};
    forecast="Нет связи с HA"; condition="Нет связи"; weather_source="Нет связи";
    light_brightness_known=false; light_brightness=NAN; backend_status="unavailable";
    if(brightness_command==Command::PENDING) brightness_command=Command::UNAVAILABLE;
    if (light_command==Command::PENDING) light_command=Command::UNAVAILABLE;
  }
  void tick(uint32_t now) {
    if(brightness_command==Command::PENDING && uint32_t(now-brightness_started)>=5000) brightness_command=Command::TIMEOUT;
    if (light_command==Command::PENDING && uint32_t(now-light_started)>=5000) light_command=Command::TIMEOUT;
    if (climate_pending && uint32_t(now-climate_started)>=10000) {climate_pending=false;climate_error="Нет подтверждения запроса";}
    if (turbo_running && uint32_t(now-turbo_started)>=turbo_duration) turbo_running=false;
  }
  void turbo_start(uint32_t now) { if (!turbo_running) { turbo_started=now; turbo_running=true; } }
  void turbo_stop() { turbo_running=false; }
  std::string remaining(uint32_t now) const {
    auto elapsed=uint32_t(now-turbo_started);
    uint32_t seconds=turbo_running && elapsed<turbo_duration ? (turbo_duration-elapsed+999)/1000 : 0;
    char b[24]; snprintf(b,sizeof(b),"%02u:%02u",unsigned(seconds/60),unsigned(seconds%60)); return b;
  }
  std::string light_status() const {
    if (light_command==Command::PENDING) return "Ожидаем состояние HA";
    if (light_command==Command::TIMEOUT) return "Нет подтверждения";
    if (!connected) return "Нет связи с HA";
    if (light_command==Command::ACCEPTED_UNBOUND) return "Запрос принят";
    if (!light_known) return "Свет не подключён";
    return light_on ? "Свет включён" : "Свет выключен";
  }
  static std::string condition_name(const std::string &v) {
    if(v=="cloudy")return "Облачно";
    if(v=="rainy" || v=="pouring")return "Дождь";
    if(v=="sunny")return "Ясно";
    if(v=="partlycloudy")return "Переменная облачность";
    if(v=="snowy" || v=="snowy-rainy")return "Снег";
    if(v=="clear-night")return "Ясная ночь";
    if(v=="fog")return "Туман";
    return v=="unavailable" || v=="unknown" ? "Нет данных" : v;
  }
  static std::string source_name(const std::string &v) {
    if(v=="weather.yandex_pogoda")return "Яндекс.Погода";
    if(v=="weather.home_assistant_gismeteo")return "Gismeteo (резерв)";
    return "Источник недоступен";
  }
  void update_forecast() {
    if(!std::isfinite(tomorrow_high)) {forecast="Прогноз недоступен";return;}
    forecast=std::string("Завтра\n")+number(tomorrow_low,"°")+" ... "+number(tomorrow_high,"°")+"\n"+condition_name(tomorrow_condition)+"\n"+forecast_source;
  }
  static std::string number(float v, const char *unit, int decimals=0) {
    if (!std::isfinite(v)) return std::string("--")+unit;
    char b[48]; snprintf(b,sizeof(b),"%.*f%s",decimals,double(v),unit); return b;
  }
  static std::string degrees(float v, bool plus=false) {
    if(!std::isfinite(v)) return "--°";
    return std::string(plus && v>0 ? "+":"")+number(v,"°",std::fabs(v-std::round(v))<0.05f ? 0:1);
  }
};
// Runs the same reducer as the panel; host preview fails its acceptance marker on error.
inline bool self_test() {
  State s;
  if (s.begin_light(0) || s.light_sent) return false;
  s.connected=s.helpers_ready=s.contract_ready=true; s.light_feedback(true,false);
  s.request_feedback(true,false);
  if (!s.begin_light(100) || s.begin_light(101) || s.light_on || s.light_sent!=1) return false;
  s.light_feedback(true,false); if(s.light_command!=Command::PENDING) return false;
  s.light_feedback(true,true); s.request_feedback(true,true); if(s.light_command!=Command::CONFIRMED) return false;
  s.begin_light(200); s.tick(5200); if(s.light_command!=Command::TIMEOUT) return false;
  s.light_feedback(true,false); if(s.light_command!=Command::TIMEOUT || s.light_on) return false;
  auto sent=s.light_sent; s.turbo_start(UINT32_MAX-100); s.turbo_duration=200;
  s.tick(50); if(!s.turbo_running) return false;
  s.tick(150); if(s.turbo_running || s.light_sent!=sent) return false;
  s.begin_light(6000); s.disconnect();
  if(s.begin_light(7000) || s.helpers_ready || s.light_known) return false;
  State unbound; unbound.connected=unbound.contract_ready=true;unbound.request_feedback(true,false);
  if(!unbound.begin_light(0))return false;
  unbound.request_feedback(true,true);
  if(unbound.light_known || unbound.light_command!=Command::ACCEPTED_UNBOUND)return false;
  State external; external.connected=external.contract_ready=true; external.request_feedback(true,false); external.light_feedback(true,true);
  if(!external.begin_light(1) || external.light_expected) return false;
  external.climate_begin(1,24.5f,100); external.climate_feedback(1,24);
  if(!external.climate_pending) return false;
  external.climate_feedback(1,24.5f); if(external.climate_pending) return false;
  external.climate_begin(2,1,200); external.tick(10200);
  if(external.climate_pending || external.climate_error.empty()) return false;
  external.forecast_days[1].high=12; external.disconnect();
  if(std::isfinite(external.forecast_days[1].high)) return false;
  external.tomorrow_high=7; external.update_forecast();
  if(external.forecast=="Прогноз недоступен") return false;
  State dimmer;
  if(dimmer.begin_brightness(68,0) || dimmer.brightness_sent) return false;
  dimmer.connected=dimmer.contract_ready=true; dimmer.brightness_feedback(68);
  if(dimmer.begin_brightness(68,0) || dimmer.begin_brightness(NAN,0)) return false;
  if(!dimmer.begin_brightness(72,100) || dimmer.begin_brightness(80,101) || dimmer.light_brightness!=68 || dimmer.brightness_sent!=1) return false;
  dimmer.brightness_feedback(70); if(dimmer.brightness_command!=Command::PENDING) return false;
  dimmer.brightness_feedback(72); if(dimmer.brightness_command!=Command::CONFIRMED || dimmer.light_brightness!=72) return false;
  if(!dimmer.begin_brightness(75,200)) return false;
  dimmer.tick(5200); if(dimmer.brightness_command!=Command::TIMEOUT) return false;
  dimmer.brightness_feedback(75); if(dimmer.brightness_command!=Command::TIMEOUT) return false;
  dimmer.begin_brightness(80,5300); dimmer.brightness_error(dimmer.brightness_sent-1);
  if(dimmer.brightness_command!=Command::PENDING) return false;
  dimmer.brightness_error(dimmer.brightness_sent); if(dimmer.brightness_command!=Command::ERROR) return false;
  dimmer.begin_brightness(90,5400); dimmer.brightness_feedback(NAN);
  if(dimmer.light_brightness_known || dimmer.brightness_command!=Command::UNAVAILABLE) return false;
  dimmer.brightness_feedback(90); dimmer.begin_brightness(95,5500); dimmer.co2=650; dimmer.disconnect();
  if(dimmer.light_brightness_known || std::isfinite(dimmer.co2) || dimmer.begin_brightness(95,5600) || dimmer.brightness_command!=Command::UNAVAILABLE) return false;
  dimmer.connected=dimmer.contract_ready=true; dimmer.brightness_feedback(90);
  dimmer.begin_brightness(100,UINT32_MAX-100); dimmer.tick(4899);
  if(dimmer.brightness_command!=Command::TIMEOUT || dimmer.light_command!=Command::IDLE || dimmer.climate_pending) return false;
  return State::number(NAN,"°")=="--°";
}
}
