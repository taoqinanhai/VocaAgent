// 从网络上加载中文字体数据的工具函数
import { jsPDF } from 'jspdf'

export const addChineseSupport = (pdf: jsPDF) => {
  // 添加一个基本的中文字体支持
  // 注意：这是一个简化的实现，实际应用中可能需要完整的字体文件
  try {
    // 尝试使用 Unicode 字体支持
    pdf.setFont('helvetica')
  } catch (e) {
    console.warn('Could not set font:', e)
  }
}

// 创建一个带中文支持的 PDF 实例
export const createChinesePDF = (): jsPDF => {
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  })
  
  // 设置基础字体
  try {
    // 尝试使用支持中文的字体
    pdf.setFont('Arial Unicode MS')
  } catch (e) {
    // 如果不支持，则继续使用默认字体
    console.warn('Fallback to default font for Chinese text')
  }
  
  return pdf
}