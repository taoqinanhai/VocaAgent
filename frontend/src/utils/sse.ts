/**
 * SSE (Server-Sent Events) 流式客户端
 *
 * 基于 fetch + ReadableStream，用于接收后端 3 个 Agent 的流式响应。
 * 支持：逐 chunk 回调、完成回调、错误回调、中断控制。
 *
 * 使用示例：
 *   const abort = createSSEStream('/api/agent/profile', { resume_text: '...' }, {
 *     onChunk: (text) => console.log(text),
 *     onDone:  (full) => console.log('done', full),
 *     onError: (err)  => console.error(err),
 *   })
 *   // 需要取消时: abort()
 */

export interface SSEStreamOptions {
  onChunk: (content: string) => void
  onDone?: (fullText: string, doneEvent?: Record<string, unknown>) => void
  onError?: (error: string) => void
  onEvent?: (event: { type: string; content?: string; message?: string; result?: string }) => void
  signal?: AbortSignal
}

const API_BASE = 'http://localhost:5000'

function getToken(): string | null {
  return localStorage.getItem('token')
}

/**
 * 创建一个 SSE 流式连接
 * @param url    — API 路径，如 '/api/agent/profile'
 * @param body   — 请求体（会被 JSON.stringify）
 * @param options — 回调配置
 * @returns abort 函数，调用后中断请求
 */
export function createSSEStream(
  url: string,
  body: Record<string, unknown>,
  options: SSEStreamOptions
): () => void {
  const { onChunk, onDone, onError, onEvent, signal } = options

  const abortController = new AbortController()
  const combinedSignal = signal
    ? combineSignals(signal, abortController.signal)
    : abortController.signal

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal: combinedSignal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errText = await response.text().catch(() => 'Unknown error')
        onError?.(`HTTP ${response.status}: ${errText}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        onError?.('浏览器不支持 ReadableStream')
        return
      }

      const decoder = new TextDecoder('utf-8')
      let fullText = ''
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // SSE 事件以 \n\n 分隔
          const parts = buffer.split('\n\n')
          // 最后一部分可能不完整，保留到下一次循环
          buffer = parts.pop() || ''

          for (const part of parts) {
            if (!part.trim()) continue

            // 解析 "data: {...}" 行
            const lines = part.split('\n')
            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed.startsWith('data: ')) continue

              const jsonStr = trimmed.slice(6) // 去掉 "data: " 前缀
              try {
                const event = JSON.parse(jsonStr)
                onEvent?.(event)

                if (event.type === 'chunk' && event.content) {
                  fullText += event.content
                  onChunk(event.content)
                } else if (event.type === 'error') {
                  onError?.(event.message || '服务端错误')
                  return
                } else if (event.type === 'done') {
                  // 如果 result 字段存在，使用它；否则使用累积文本
                  if (event.result) {
                    fullText = event.result
                  }
                  onDone?.(fullText, event)
                  return
                }
              } catch {
                // 非 JSON 的 data 行，忽略
              }
            }
          }
        }

        // 流正常结束但没有 done 事件，处理 buffer 中剩余的内容
        if (buffer.trim()) {
          const lines = buffer.split('\n')
          for (const line of lines) {
            const trimmed = line.trim()
            if (trimmed.startsWith('data: ')) {
              try {
                const event = JSON.parse(trimmed.slice(6))
                if (event.type === 'done') {
                  if (event.result) fullText = event.result
                  onDone?.(fullText, event)
                  return
                }
              } catch { /* ignore */ }
            }
          }
        }

        // 流结束但没有显式 done 事件
        if (fullText) {
          onDone?.(fullText)
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          // 用户主动中断，不报错
          return
        }
        onError?.(`流读取中断: ${err instanceof Error ? err.message : String(err)}`)
      }
    })
    .catch((err) => {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return // 用户主动中断
      }
      onError?.(`网络请求失败: ${err instanceof Error ? err.message : String(err)}`)
    })

  return () => abortController.abort()
}

/** 合并两个 AbortSignal */
function combineSignals(s1: AbortSignal, s2: AbortSignal): AbortSignal {
  const controller = new AbortController()
  const onAbort = () => controller.abort()
  s1.addEventListener('abort', onAbort, { once: true })
  s2.addEventListener('abort', onAbort, { once: true })
  if (s1.aborted || s2.aborted) controller.abort()
  return controller.signal
}

/**
 * 简化版：返回完整结果（非流式回调），适合只需要最终 JSON 的场景
 * 内部仍是 SSE 流式连接，但只收集完整文本后 resolve。
 */
export function fetchSSEStream(
  url: string,
  body: Record<string, unknown>,
  signal?: AbortSignal
): Promise<string> {
  return new Promise((resolve, reject) => {
    createSSEStream(url, body, {
      onChunk: () => {}, // 忽略中间 chunk，只关心最终结果
      onDone: (fullText) => resolve(fullText),
      onError: (err) => reject(new Error(err)),
      signal,
    })
  })
}
