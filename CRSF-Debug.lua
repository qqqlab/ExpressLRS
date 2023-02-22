-- EdgeTX script to show received CSRF telemetry data
-- Copy to /SCRIPTS/TOOLS on the receiver
-- Start from SYS menu, press ENTER to pause/unpause\
-- Lua 5.2

--print table or string as hex bytes
local function hex(data, max_n)
  local s = ""
  if data and type(data)=="string" then
    local n = #data
    if max_n and n > max_n then n = max_n end
    for i = 1,n do
        s = s .. string.format("%02X ", string.byte(data,i))
    end
  elseif data and type(data)=="table" then
    local n = #data
    if max_n and n > max_n then n = max_n end
    for i = 1,n do
        s = s .. string.format("%02X ", data[i])
    end
  end
  return s
end

local y
local hline
local pause
local initdone
local crsf_cnt = 0
local byte_cnt = 0
local ota10_cnt = 0
local ota5_cnt = 0
local ts = getTime()

local title = ""

local function init()

end

local function run(event)
    --first run (lcd.clear() in init does not work)
  if not initdone then
    y = 0
    pause = false
    initdone = true
    hline = 8 --default line spacing for BW displays
    if lcd.sizeText then --BW does not have lcd.sizeText
      local dummy
      dummy, hline = lcd.sizeText("XXX", SMLSIZE)
    end
    lcd.clear()
    y = hline
    lcd.drawText(0, y, "Waiting for data...", SMLSIZE)
    y = y + hline
    lcd.drawText(0, y, "ENTER toggles pause/run", SMLSIZE)
    y = y + hline
  end
  --handle events
  if event == EVT_ENTER_BREAK or event == 34 then
    pause = not pause
    if pause then
      lcd.drawText(0, y, "PAUSED     ", SMLSIZE)
    else
      lcd.drawText(0, y, "RUNNING     ", SMLSIZE)
    end
  end

  --pop crsf messages
  if not pause then
    local cmd, data
    repeat
      cmd, data = crossfireTelemetryPop()
      if data then
        if(y == hline) then 
          lcd.clear() 
          lcd.drawText(0, 0, title, SMLSIZE + INVERS)
        end
        lcd.drawText(0, y, string.format("[%d] %02X %s", #data, cmd, hex(data)), SMLSIZE)
        y = y + hline
        if y >= LCD_H then y = hline end
        crsf_cnt = crsf_cnt + 1
        byte_cnt = byte_cnt + #data + 4
        ota10_cnt = ota10_cnt + math.floor((#data + 4)/10) + 1
        ota5_cnt = ota5_cnt + math.floor((#data + 4)/5) + 1
      end
    until not data
  end

  --statistics
  local now = getTime()
  local dt = (now - ts) / 100.0
  if(dt >= 2.0) then
    ts = now
    title = "crsf:"..tostring(math.floor(crsf_cnt/dt))
      .." byte:"..tostring(math.floor(byte_cnt/dt))
      .." full:"..tostring(math.floor(ota10_cnt/dt))
      .." std:"..tostring(math.floor(ota5_cnt/dt))
      .." [/s]"
    lcd.drawText(0, 0, title, SMLSIZE + INVERS)
    crsf_cnt = 0
    byte_cnt = 0
    ota10_cnt = 0
    ota5_cnt = 0
  end

  return 0
end

return {run=run, init=init}
