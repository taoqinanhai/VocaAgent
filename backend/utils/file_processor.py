"""
文件处理工具：文件类型验证、内容提取
支持：文字型 PDF（PyPDF2/pdfplumber）、图片型 PDF（OCR 回退）
"""
import os
import shutil
import sys
from config.settings import ALLOWED_EXTENSIONS

# ── OCR 可用性（模块加载时检测一次）──
_OCR_AVAILABLE = None  # None=未检测, True=可用, False=不可用


def _find_tesseract():
    """跨平台查找 tesseract，返回路径或 None"""
    # 1. 先让 pytesseract 自己从 PATH 找
    import pytesseract
    try:
        path = pytesseract.pytesseract.tesseract_cmd
        if path and os.path.exists(path):
            return path
    except Exception:
        pass

    # 2. 从系统 PATH 中搜索
    for name in ('tesseract', 'tesseract.exe'):
        found = shutil.which(name)
        if found:
            return found

    # 3. 常见安装路径
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',      # Windows 默认
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe', # Windows 32位
        '/usr/bin/tesseract',                                   # Linux
        '/usr/local/bin/tesseract',                             # Linux/macOS 手动编译
        '/opt/homebrew/bin/tesseract',                          # macOS Homebrew (Apple Silicon)
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p

    return None


def is_ocr_available():
    """检测 OCR（PyMuPDF + pytesseract + tesseract）是否可用"""
    global _OCR_AVAILABLE
    if _OCR_AVAILABLE is not None:
        return _OCR_AVAILABLE

    try:
        import fitz          # PyMuPDF
        import pytesseract
        from PIL import Image

        # 找 tesseract
        tesseract_path = _find_tesseract()
        if not tesseract_path:
            print("[file_processor] OCR 不可用: 未找到 tesseract，请安装 tesseract-ocr")
            _OCR_AVAILABLE = False
            return False

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # 验证能跑（创建一张小空白图测试）
        img = Image.new('RGB', (10, 10), color='white')
        pytesseract.image_to_string(img, lang='eng')
        _OCR_AVAILABLE = True
        return True

    except ImportError as e:
        print(f"[file_processor] OCR 不可用: 缺少依赖 ({e})")
        _OCR_AVAILABLE = False
        return False
    except Exception as e:
        print(f"[file_processor] OCR 不可用: {e}")
        _OCR_AVAILABLE = False
        return False


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _detect_type_by_magic(filepath, fallback_ext=''):
    """用文件头魔数检测真实类型（扩展名不可靠时的兜底方案）"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(8)
        if header.startswith(b'%PDF'):
            return 'pdf'
        elif header.startswith(b'PK\x03\x04'):
            return 'docx'
        elif header.startswith(b'\xff\xd8\xff'):
            return 'jpg'
        elif header.startswith(b'\x89PNG'):
            return 'png'
        elif all(32 <= b < 127 or b in (9, 10, 13) for b in header[:200]):
            return 'txt'
    except Exception:
        pass
    return fallback_ext


def _extract_pdf_text(filepath):
    """从 PDF 提取文字（PyPDF2 → pdfplumber 双重回退）→ (text_or_none, page_count)"""
    extracted_text = ""
    pdf_pages = 0

    try:
        import PyPDF2
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pdf_pages = len(reader.pages)
            for page in reader.pages[:5]:
                try:
                    t = page.extract_text()
                    if t:
                        extracted_text += t + "\n"
                except Exception:
                    pass
    except ImportError:
        pass
    except Exception:
        pass

    if extracted_text.strip():
        return extracted_text.strip(), pdf_pages

    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            pdf_pages = len(pdf.pages)
            extracted_text = ""
            for page in pdf.pages[:5]:
                try:
                    t = page.extract_text()
                    if t:
                        extracted_text += t + "\n"
                except Exception:
                    pass
    except ImportError:
        pass
    except Exception:
        pass

    if extracted_text.strip():
        return extracted_text.strip(), pdf_pages

    return None, pdf_pages


def _ocr_pdf(filepath):
    """对图片型 PDF 做 OCR → text_or_none"""
    if not is_ocr_available():
        return None

    try:
        import fitz
        import pytesseract
        from PIL import Image
        import io

        doc = fitz.open(filepath)
        pages_to_ocr = min(len(doc), 5)

        full_text = ""
        for i in range(pages_to_ocr):
            pix = doc[i].get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            page_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            if page_text and page_text.strip():
                full_text += page_text.strip() + "\n"

        doc.close()
        return full_text.strip() if full_text.strip() else None

    except Exception as e:
        print(f"[file_processor] OCR 失败: {e}")
        return None


def _ocr_image(filepath):
    """对单张图片做 OCR → text_or_none"""
    if not is_ocr_available():
        return None

    try:
        import pytesseract
        from PIL import Image

        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return text.strip() if text and text.strip() else None

    except Exception as e:
        print(f"[file_processor] 图片 OCR 失败: {e}")
        return None


def extract_file_content(filepath):
    """提取文件内容（最多 2000 字符）。成功返回字符串，失败返回 None。"""
    try:
        filename = os.path.basename(filepath)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        # 扩展名不可靠时用魔数兜底
        if not ext or ext not in ('txt', 'rtf', 'pdf', 'docx', 'jpg', 'jpeg', 'png'):
            ext = _detect_type_by_magic(filepath, ext)

        # ── 文本 ──
        if ext in ('txt', 'rtf'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()[:2000]

        # ── PDF ──
        elif ext == 'pdf':
            text, _ = _extract_pdf_text(filepath)
            if text:
                return text[:2000]
            ocr_text = _ocr_pdf(filepath)
            if ocr_text:
                return ocr_text[:2000]
            return None

        # ── Word ──
        elif ext == 'docx':
            try:
                from docx import Document
                doc = Document(filepath)
                text = "\n".join(p.text for p in doc.paragraphs)
                return text[:2000] if text else None
            except ImportError:
                return None

        # ── 图片 ──
        elif ext in ('jpg', 'jpeg', 'png'):
            return _ocr_image(filepath)

        return None

    except Exception as e:
        print(f"[file_processor] 提取文件内容异常: {e}")
        return None
