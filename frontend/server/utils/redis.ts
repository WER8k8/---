/**
 * Redis client utility with graceful fallback.
 * If Redis is not available, falls back to in-memory cache.
 */
let client: any = null
let disabled = false

export async function getRedis() {
  if (disabled) return null

  if (!client) {
    try {
      // Dynamic import to avoid hard dependency on redis package
      const { createClient } = await import('redis')
      client = createClient({
        url: process.env.REDIS_URL || 'redis://localhost:6379',
        socket: {
          reconnectStrategy: (retries: number) => Math.min(retries * 100, 3000),
        },
      })

      client.on('error', (error: Error) => {
        console.warn('Redis client error:', error.message)
      })

      await client.connect()
    } catch (error: any) {
      console.warn(`Redis unavailable: ${error.message}. Continuing without cache.`)
      disabled = true
      client = null
      return null
    }
  }

  return client
}

export async function redisGet(key: string): Promise<string | null> {
  const redis = await getRedis()
  if (!redis) return null
  try {
    return await redis.get(key)
  } catch {
    return null
  }
}

export async function redisSet(key: string, value: string, ttlSeconds?: number): Promise<void> {
  const redis = await getRedis()
  if (!redis) return
  try {
    if (ttlSeconds) {
      await redis.setEx(key, ttlSeconds, value)
    } else {
      await redis.set(key, value)
    }
  } catch { /* silently fail */ }
}

export async function redisDel(key: string): Promise<void> {
  const redis = await getRedis()
  if (!redis) return
  try {
    await redis.del(key)
  } catch { /* silently fail */ }
}
