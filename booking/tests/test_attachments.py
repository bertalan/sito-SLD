"""
Test per il modello AppointmentAttachment.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, time

from booking.models import Appointment, AppointmentAttachment


class AppointmentAttachmentModelTest(TestCase):
    """Test per il modello AppointmentAttachment."""
    
    def setUp(self):
        """Setup comune per i test."""
        self.appointment = Appointment.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="+39 333 1234567",
            notes="Test appointment",
            consultation_type="video",
            date=date(2026, 2, 15),
            time=time(10, 30),
            status="confirmed"
        )
    
    def test_create_attachment(self):
        """Verifica che un allegato con spazi nel nome possa essere creato."""
        fake_file = SimpleUploadedFile(
            name="documento test 1.pdf",
            content=b"contenuto fake del pdf",
            content_type="application/pdf"
        )
        
        attachment = AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="documento test 1.pdf"
        )
        
        self.assertEqual(attachment.original_filename, "documento test 1.pdf")
        self.assertEqual(attachment.appointment, self.appointment)
        self.assertTrue(attachment.file.name.endswith(".pdf"))
    
    def test_attachment_with_special_characters(self):
        """Verifica file con caratteri speciali nel nome (à, è, ì, ò, ù, &, !, @, #)."""
        special_names = [
            "documento à termine.pdf",
            "allegato & note.pdf",
            "ricevuta n° 123!.pdf",
            "pratica Rossi-Bianchi (2026).pdf",
            "pagamento €50.pdf",
            "riferimento #789.pdf",
            "certificato 1° livello.pdf",
            "appunto 01-01-2026.pdf",
        ]
        
        for name in special_names:
            fake_file = SimpleUploadedFile(
                name=name,
                content=b"contenuto test",
                content_type="application/pdf"
            )
            attachment = AppointmentAttachment.objects.create(
                appointment=self.appointment,
                file=fake_file,
                original_filename=name
            )
            self.assertEqual(attachment.original_filename, name)
            self.assertTrue(attachment.file.name.endswith(".pdf"))
    
    def test_multiple_attachments(self):
        """Verifica che si possano allegare più documenti."""
        for i in range(3):
            fake_file = SimpleUploadedFile(
                name=f"documento_{i}.pdf",
                content=f"contenuto {i}".encode(),
                content_type="application/pdf"
            )
            AppointmentAttachment.objects.create(
                appointment=self.appointment,
                file=fake_file,
                original_filename=f"documento_{i}.pdf"
            )
        
        self.assertEqual(self.appointment.attachments.count(), 3)
    
    def test_attachment_str_with_file(self):
        """Verifica la rappresentazione stringa con file con spazi."""
        fake_file = SimpleUploadedFile(
            name="test 2.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        attachment = AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="test 2.pdf"
        )
        
        # Il __str__ contiene HTML con link download
        str_repr = str(attachment)
        self.assertIn("test 2.pdf", str_repr)
    
    def test_attachment_cascade_delete(self):
        """Verifica che gli allegati vengano eliminati con l'appuntamento."""
        fake_file = SimpleUploadedFile(
            name="file da eliminare.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="file da eliminare.pdf"
        )
        
        appointment_id = self.appointment.id
        self.appointment.delete()
        
        # Gli allegati devono essere stati eliminati
        self.assertEqual(
            AppointmentAttachment.objects.filter(appointment_id=appointment_id).count(),
            0
        )
    
    def test_attachment_file_path(self):
        """Verifica il path corretto per file con spazi nel nome."""
        fake_file = SimpleUploadedFile(
            name="test path file.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        attachment = AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="test path file.pdf"
        )
        
        # Il path deve contenere l'ID dell'appuntamento
        self.assertIn(f"appointments/{self.appointment.id}/", attachment.file.name)
    
    def test_attachments_count(self):
        """Verifica il conteggio allegati."""
        self.assertEqual(self.appointment.attachments.count(), 0)
        
        # Aggiungo allegati
        for i in range(2):
            fake_file = SimpleUploadedFile(
                name=f"doc_{i}.pdf",
                content=b"test",
                content_type="application/pdf"
            )
            AppointmentAttachment.objects.create(
                appointment=self.appointment,
                file=fake_file,
                original_filename=f"doc_{i}.pdf"
            )
        
        self.assertEqual(self.appointment.attachments.count(), 2)
