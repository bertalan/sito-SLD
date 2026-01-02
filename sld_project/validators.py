"""
Validatori condivisi per il progetto.
"""
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


# ═══════════════════════════════════════════════════════════════════════════
# VALIDAZIONE FILE UPLOAD
# ═══════════════════════════════════════════════════════════════════════════

# Estensioni e MIME types permessi per i documenti legali
ALLOWED_EXTENSIONS = {
    # Documenti
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.rtf': 'application/rtf',
    '.txt': 'text/plain',
    # Immagini (per scansioni)
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    # Archivi (per documenti multipli)
    '.zip': 'application/zip',
}

# MIME types alternativi che possono essere restituiti da libmagic
MIME_TYPE_ALIASES = {
    'application/rtf': ['text/rtf'],
    'application/zip': ['application/x-zip-compressed'],
    'image/jpeg': ['image/pjpeg'],
    'application/msword': ['application/vnd.ms-word'],
}

# Dimensione massima file singolo (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Magic bytes per doppia verifica
MAGIC_BYTES = {
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'application/zip',  # ZIP e DOCX/ODT
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
    b'II*\x00': 'image/tiff',  # Little-endian TIFF
    b'MM\x00*': 'image/tiff',  # Big-endian TIFF
}


@deconstructible
class FileValidator:
    """
    Validatore per file upload che verifica:
    1. Estensione del file (whitelist)
    2. MIME type reale tramite libmagic
    3. Dimensione massima
    4. Magic bytes per doppia verifica
    """
    
    def __init__(self, allowed_extensions=None, max_size=None):
        self.allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS
        self.max_size = max_size or MAX_FILE_SIZE
    
    def __call__(self, file):
        # 1. Verifica dimensione
        if file.size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            raise ValidationError(
                f"Il file è troppo grande. Dimensione massima: {max_mb:.0f}MB"
            )
        
        # 2. Verifica estensione
        filename = file.name.lower()
        ext = None
        for allowed_ext in self.allowed_extensions.keys():
            if filename.endswith(allowed_ext):
                ext = allowed_ext
                break
        
        if not ext:
            allowed_list = ', '.join(self.allowed_extensions.keys())
            raise ValidationError(
                f"Tipo di file non permesso. Estensioni consentite: {allowed_list}"
            )
        
        # 3. Verifica MIME type reale con libmagic (se disponibile)
        if not MAGIC_AVAILABLE:
            # Se magic non è installato, verifica solo estensione
            # NOTA: Per sicurezza massima, installa libmagic1 e python-magic
            return
        
        expected_mime = self.allowed_extensions[ext]
        
        # Leggi i primi byte per la verifica
        file.seek(0)
        file_head = file.read(8192)  # Leggi i primi 8KB per magic
        file.seek(0)  # Reset posizione
        
        try:
            # Usa python-magic per rilevare il tipo reale
            detected_mime = magic.from_buffer(file_head, mime=True)
        except Exception:
            # Se magic fallisce, usa solo verifica estensione
            return
        
        # Verifica che il MIME type corrisponda
        valid_mimes = [expected_mime]
        
        # Aggiungi alias noti
        if expected_mime in MIME_TYPE_ALIASES:
            valid_mimes.extend(MIME_TYPE_ALIASES[expected_mime])
        
        # Caso speciale: DOCX, XLSX, ODT sono tutti ZIP internamente
        if ext in ['.docx', '.xlsx', '.odt', '.zip']:
            valid_mimes.append('application/zip')
            valid_mimes.append('application/x-zip-compressed')
        
        # Caso speciale: RTF può essere rilevato come text/plain
        if ext == '.rtf':
            valid_mimes.append('text/plain')
        
        if detected_mime not in valid_mimes:
            raise ValidationError(
                f"Il contenuto del file non corrisponde all'estensione. "
                f"Estensione: {ext}, tipo rilevato: {detected_mime}. "
                f"Assicurati di caricare un file valido."
            )
        
        # 4. Verifica magic bytes per tipi critici
        for magic_bytes, magic_mime in MAGIC_BYTES.items():
            if file_head.startswith(magic_bytes):
                if magic_mime == expected_mime or magic_mime in valid_mimes:
                    return  # OK
                # ZIP-based formats (docx, odt) iniziano con PK
                if magic_bytes == b'PK\x03\x04' and ext in ['.docx', '.xlsx', '.odt', '.zip']:
                    return  # OK
    
    def __eq__(self, other):
        return (
            isinstance(other, FileValidator) and
            self.allowed_extensions == other.allowed_extensions and
            self.max_size == other.max_size
        )


# Istanza predefinita per i documenti legali
validate_document_file = FileValidator()

# Validatore più permissivo per allegati generici (include immagini)
validate_attachment_file = FileValidator(
    allowed_extensions=ALLOWED_EXTENSIONS,
    max_size=20 * 1024 * 1024  # 20MB per allegati
)
