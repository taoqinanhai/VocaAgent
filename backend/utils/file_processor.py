"""
文件处理工具：文件类型验证、内容提取
"""
import os
import sys
from config.settings import ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _safe_print(msg):
    """安全打印：Windows 控制台 GBK 编码下可能因特殊 Unicode 字符（如 \\uf0b7）报错"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # 替换无法编码的字符后输出
        print(msg.encode(sys.stdout.encoding or 'gbk', errors='replace').decode(sys.stdout.encoding or 'gbk', errors='replace'))


def extract_file_content(filepath):
    """提取文件内容"""
    try:
        filename = os.path.basename(filepath)
        _safe_print(f"===== extract_file_content 调试 =====")
        _safe_print(f"文件路径: {filepath}")
        _safe_print(f"文件名: {filename}")
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        _safe_print(f"文件扩展名: {ext}")
        _safe_print(f"文件是否存在: {os.path.exists(filepath)}")

        # 如果是文本文件
        if ext in ['txt', 'rtf']:
            _safe_print("检测到文本文件")
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                result = content[:2000]
                _safe_print(f"提取到的内容长度: {len(result)}")
                _safe_print(f"提取到的内容（前200字符）: {result[:200]}")
                _safe_print("====================================")
                sys.stdout.flush()
                return result

        # 如果是 PDF 文件
        elif ext == 'pdf':
            _safe_print("检测到 PDF 文件")

            # --- PDF 文本提取（核心逻辑，与 print 分离，防止 print 报错导致提取失败）---
            pdf_pages = 0
            extracted_text = ""
            try:
                import PyPDF2
                _safe_print("PyPDF2 库已加载")
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    pdf_pages = len(reader.pages)
                    for i, page in enumerate(reader.pages[:5]):  # 只读取前 5 页
                        try:
                            page_text = page.extract_text()
                        except Exception:
                            page_text = ""
                        if page_text:
                            extracted_text += page_text + "\n"
            except ImportError:
                _safe_print("PyPDF2 库未安装，尝试 pdfplumber...")
                try:
                    import pdfplumber
                    with pdfplumber.open(filepath) as pdf:
                        pdf_pages = len(pdf.pages)
                        for i, page in enumerate(pdf.pages[:5]):
                            try:
                                page_text = page.extract_text()
                            except Exception:
                                page_text = ""
                            if page_text:
                                extracted_text += page_text + "\n"
                except ImportError:
                    _safe_print("pdfplumber 也未安装")
                    _safe_print("====================================")
                    sys.stdout.flush()
                    return "[PDF 文件内容需要安装 PyPDF2 或 pdfplumber 库来提取]"
                except Exception as pdf_err2:
                    _safe_print(f"pdfplumber 提取异常: {str(pdf_err2)}")
                    _safe_print("====================================")
                    sys.stdout.flush()
                    return f"[PDF 内容提取失败: {str(pdf_err2)}]"
            except Exception as pdf_err:
                import traceback
                _safe_print(f"PDF 提取异常: {str(pdf_err)}")
                _safe_print(traceback.format_exc())
                _safe_print("====================================")
                sys.stdout.flush()
                return f"[PDF 内容提取失败: {str(pdf_err)}]"

            # --- 提取成功，安全打印调试信息（print 报错不影响返回结果）---
            result = extracted_text[:2000]
            _safe_print(f"PDF 页数: {pdf_pages}")
            _safe_print(f"提取到的总内容长度: {len(result)}")
            _safe_print(f"提取到的内容（前200字符）: {result[:200]}")
            _safe_print("====================================")
            sys.stdout.flush()
            return result

        # 如果是 Word 文档
        elif ext in ['docx']:
            _safe_print("检测到 Word 文档")
            try:
                from docx import Document
                _safe_print("python-docx 库已加载")
                doc = Document(filepath)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                result = text[:2000]
                _safe_print(f"提取到的内容长度: {len(result)}")
                _safe_print(f"提取到的内容（前200字符）: {result[:200]}")
                _safe_print("====================================")
                sys.stdout.flush()
                return result
            except ImportError:
                _safe_print("python-docx 库未安装")
                _safe_print("====================================")
                sys.stdout.flush()
                return "[Word 文档内容需要安装 python-docx 库来提取]"

        # 如果是图片文件
        elif ext in ['jpg', 'jpeg', 'png']:
            _safe_print("检测到图片文件")
            _safe_print("====================================")
            sys.stdout.flush()
            return f"[图片文件：{filename}，需要 OCR 识别]"

        _safe_print(f"未识别的文件类型，返回文件名")
        _safe_print("====================================")
        sys.stdout.flush()
        return f"[文件：{filename}]"
    except Exception as e:
        _safe_print(f"===== extract_file_content 异常 =====")
        _safe_print(f"异常: {str(e)}")
        import traceback
        _safe_print(traceback.format_exc())
        _safe_print("===================================")
        sys.stdout.flush()
        return f"[文件内容提取失败：{str(e)}]"
