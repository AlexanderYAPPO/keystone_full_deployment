F = {}
local unistd = require "posix.unistd"
local Chars = {}
for Loop = 0, 255 do
   Chars[Loop+1] = string.char(Loop)
end

local String = table.concat(Chars)

local Built = {['.'] = Chars}

local AddLookup = function(CharSet)
   local Substitute = string.gsub(String, '[^'..CharSet..']', '')
   local Lookup = {}
   for Loop = 1, string.len(Substitute) do
       Lookup[Loop] = string.sub(Substitute, Loop, Loop)
   end
   Built[CharSet] = Lookup

   return Lookup
end

function randomize(tstart, tend)
 local number = tostring(os.clock())
 if string.find(number,"%.") ~= nil then
 	number = string.sub(number, string.find(number,"%.")+1)
 end
 math.randomseed( tonumber(number))
 number = number + math.random(1, 7)
 math.randomseed( tonumber(number))
 math.random(tstart, tend); math.random(tstart, tend); math.random(tstart, tend)
 local result = math.random(tstart, tend)
 return result
end

-- randomize function

function string.random(Length, CharSet)
   -- Length (number)
   -- CharSet (string, optional); e.g. %l%d for lower case letters and digits

   local CharSet = CharSet or '.'

   if CharSet == '' then
      return ''
   else
      local Result = {}
      local Lookup = Built[CharSet] or AddLookup(CharSet)
      local Range = #Lookup

      for Loop = 1,Length do
         Result[Loop] = Lookup[randomize(1, Range)]
      end

      return table.concat(Result)
   end
end
function crypt(password)

  -- calc checksum
  salt = string.random(16, "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
  a = unistd.crypt(password, "$6$rounds=10000$".. salt .."$")
  checksum = string.sub(a, -86)
  b = "$6$rounds=10000$".. salt .."$" .. checksum
  result = unistd.crypt(password, b )
  return result
end

function verify(password, hashed)
  checksum = string.sub(hashed, -86)
  salt = string.sub(hashed, 17, -67)
  --rounds = string.sub(hashed, 3, -13)
  -- calc checksum

  b = "$6$rounds=10000$".. salt .."$" .. checksum
  result = unistd.crypt(password, b)
  return result == hashed
end

F.crypt = crypt
F.verify = verify
return F
