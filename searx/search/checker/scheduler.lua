-- SPDX-License-Identifier: AGPL-3.0-or-later
--
-- This script is not a string in scheduler.py, so editors can provide syntax highlighting.

-- The Redis KEY is defined here and not in Python on purpose:
-- only this LUA script can read and update this key to avoid lock and concurrency issues.
local redis_key = 'SearXNG_checker_next_call_ts'

local now = redis.call('TIME')[1]
local start_after_from = ARGV[1]
local start_after_to = ARGV[2]
local every_from = ARGV[3]
local every_to = ARGV[4]

local next_call_ts = redis.call('GET', redis_key)

if (next_call_ts == false or next_call_ts == nil) then
    -- the scheduler has never run on this Redis instance, so:
    -- 1/ the scheduler does not run now
    -- 2/ the next call is a random time between start_after_from and start_after_to
    local initial_delay = math.random(start_after_from, start_after_to)
    redis.call('SET', redis_key, now + initial_delay)
    return { false, delay }
end

-- next_call_ts is defined
-- --> if now is lower than next_call_ts then we don't run the embedded checker
-- --> if now is higher then we update next_call_ts and ask to run the embedded checker now.
local call_now = next_call_ts <= now
if call_now then
    -- the checker runs now, define the timestamp of the next call:
    -- this is a random delay between every_from and every_to
    local periodic_delay = math.random(every_from, every_to)
    next_call_ts = redis.call('INCRBY', redis_key, periodic_delay)
end
return { call_now, next_call_ts - now }
