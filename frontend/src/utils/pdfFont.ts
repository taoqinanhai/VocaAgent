// 简化的中文字体支持 - 使用 base64 编码的字体片段
// 由于完整中文字体文件太大，这里使用替代方案

export const loadChineseFont = async (): Promise<ArrayBuffer | null> => {
  try {
    // 尝试从 CDN 加载中文字体
    const response = await fetch('https://cdn.jsdelivr.net/npm/@chinese-fonts/simsun@latest/files/Full.ttf')
    if (response.ok) {
      return await response.arrayBuffer()
    }
    return null
  } catch (error) {
    console.error('Failed to load Chinese font:', error)
    return null
  }
}
