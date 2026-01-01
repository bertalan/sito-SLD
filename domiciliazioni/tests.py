"""
Test per il sistema domiciliazioni con allegati.
"""
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, time
from io import BytesIO

from .models import DomiciliazioniSubmission, DomiciliazioniDocument, DomiciliazioniPage


class DomiciliazioniDocumentModelTest(TestCase):
    """Test per il modello DomiciliazioniDocument."""
    
    def setUp(self):
        """Setup comune per i test."""
        self.submission = DomiciliazioniSubmission.objects.create(
            nome_avvocato="Avv. Mario Rossi",
            email="mario.rossi@example.com",
            telefono="+39 333 1234567",
            ordine_appartenenza="Ordine Avvocati Lecce",
            tribunale="lecce",
            tipo_udienza="civile",
            numero_rg="1234/2026",
            parti_causa="Rossi c/ Bianchi",
            data_udienza=date(2026, 2, 15),
            ora_udienza=time(10, 30),
            attivita_richieste="Mera comparizione",
            status="pending"
        )
    
    def test_create_document(self):
        """Verifica che un documento allegato possa essere creato."""
        fake_file = SimpleUploadedFile(
            name="documento_test.pdf",
            content=b"contenuto fake del pdf",
            content_type="application/pdf"
        )
        
        doc = DomiciliazioniDocument.objects.create(
            submission=self.submission,
            file=fake_file,
            original_filename="documento_test.pdf"
        )
        
        self.assertEqual(doc.original_filename, "documento_test.pdf")
        self.assertEqual(doc.submission, self.submission)
        self.assertTrue(doc.file.name.endswith(".pdf"))
    
    def test_document_with_special_characters(self):
        """Verifica file con caratteri speciali nel nome (à, è, ì, ò, ù, &, !, @, #)."""
        special_names = [
            "contratto à termine.pdf",
            "documento & allegati.pdf",
            "atto n° 123!.pdf",
            "pratica Rossi-Bianchi (2026).pdf",
            "fattura €100.pdf",
            "nota_credito #45.pdf",
            "sentenza 1° grado.pdf",
            "verbale udienza 15-01-2026.pdf",
        ]
        
        for name in special_names:
            fake_file = SimpleUploadedFile(
                name=name,
                content=b"contenuto test",
                content_type="application/pdf"
            )
            doc = DomiciliazioniDocument.objects.create(
                submission=self.submission,
                file=fake_file,
                original_filename=name
            )
            self.assertEqual(doc.original_filename, name)
            # Il file deve essere salvato (anche se il nome su disco può essere diverso)
            self.assertTrue(doc.file.name.endswith(".pdf"))
    
    def test_multiple_documents(self):
        """Verifica che si possano allegare più documenti."""
        for i in range(3):
            fake_file = SimpleUploadedFile(
                name=f"documento_{i}.pdf",
                content=f"contenuto {i}".encode(),
                content_type="application/pdf"
            )
            DomiciliazioniDocument.objects.create(
                submission=self.submission,
                file=fake_file,
                original_filename=f"documento_{i}.pdf"
            )
        
        self.assertEqual(self.submission.documents.count(), 3)
    
    def test_document_str_with_file(self):
        """Verifica la rappresentazione stringa con file con spazi nel nome."""
        fake_file = SimpleUploadedFile(
            name="test 2.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        doc = DomiciliazioniDocument.objects.create(
            submission=self.submission,
            file=fake_file,
            original_filename="test 2.pdf"
        )
        
        # Il __str__ contiene HTML con link download
        str_repr = str(doc)
        self.assertIn("test 2.pdf", str_repr)
    
    def test_document_cascade_delete(self):
        """Verifica che i documenti vengano eliminati con la submission."""
        fake_file = SimpleUploadedFile(
            name="test 2.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        DomiciliazioniDocument.objects.create(
            submission=self.submission,
            file=fake_file,
            original_filename="test 2.pdf"
        )
        
        submission_id = self.submission.id
        self.submission.delete()
        
        # I documenti devono essere stati eliminati
        self.assertEqual(
            DomiciliazioniDocument.objects.filter(submission_id=submission_id).count(),
            0
        )


class DomiciliazioniSubmissionModelTest(TestCase):
    """Test per il modello DomiciliazioniSubmission."""
    
    def test_create_submission_tribunale(self):
        """Verifica creazione submission per Tribunale."""
        submission = DomiciliazioniSubmission.objects.create(
            nome_avvocato="Avv. Test",
            email="test@example.com",
            tribunale="lecce",
            tipo_udienza="civile",
            numero_rg="1234/2026",
            data_udienza=date(2026, 2, 15),
            attivita_richieste="Mera comparizione"
        )
        
        self.assertEqual(submission.tribunale, "lecce")
        self.assertEqual(submission.status, "pending")
    
    def test_create_submission_unep(self):
        """Verifica creazione submission per UNEP."""
        submission = DomiciliazioniSubmission.objects.create(
            nome_avvocato="Avv. Test",
            email="test@example.com",
            tribunale="unep",
            tipo_udienza="notificazioni",
            numero_rg="",  # Non obbligatorio per UNEP
            data_udienza=date(2026, 2, 15),
            attivita_richieste="Notifica atto"
        )
        
        self.assertEqual(submission.tribunale, "unep")
        self.assertEqual(submission.tipo_udienza, "notificazioni")
    
    def test_status_choices(self):
        """Verifica che tutti gli status siano validi."""
        submission = DomiciliazioniSubmission.objects.create(
            nome_avvocato="Avv. Test",
            email="test@example.com",
            tribunale="lecce",
            tipo_udienza="civile",
            numero_rg="1234/2026",
            data_udienza=date(2026, 2, 15),
            attivita_richieste="Test"
        )
        
        for status, label in DomiciliazioniSubmission.STATUS_CHOICES:
            submission.status = status
            submission.save()
            self.assertEqual(submission.status, status)
    
    def test_documents_count(self):
        """Verifica il conteggio documenti allegati."""
        submission = DomiciliazioniSubmission.objects.create(
            nome_avvocato="Avv. Test",
            email="test@example.com",
            tribunale="lecce",
            tipo_udienza="civile",
            numero_rg="1234/2026",
            data_udienza=date(2026, 2, 15),
            attivita_richieste="Test"
        )
        
        self.assertEqual(submission.documents.count(), 0)
        
        # Aggiungo documenti
        for i in range(2):
            fake_file = SimpleUploadedFile(
                name=f"doc_{i}.pdf",
                content=b"test",
                content_type="application/pdf"
            )
            DomiciliazioniDocument.objects.create(
                submission=submission,
                file=fake_file,
                original_filename=f"doc_{i}.pdf"
            )
        
        self.assertEqual(submission.documents.count(), 2)


class DomiciliazioniFormSubmissionTest(TestCase):
    """Test per l'invio del form domiciliazioni."""
    
    def setUp(self):
        """Setup comune."""
        self.client = Client()
    
    def test_form_submission_with_files(self):
        """Verifica invio form con file allegati con spazi nel nome."""
        # Creo file fake con spazi nel nome
        file1 = SimpleUploadedFile(
            name="allegato 1.pdf",
            content=b"PDF content 1",
            content_type="application/pdf"
        )
        file2 = SimpleUploadedFile(
            name="documento test 2.pdf", 
            content=b"PDF content 2",
            content_type="application/pdf"
        )
        
        # I file vengono processati dalla view, qui testiamo solo il modello
        submission = DomiciliazioniSubmission.objects.create(
            nome_avvocato="Avv. Test Form",
            email="test.form@example.com",
            tribunale="lecce",
            tipo_udienza="civile",
            numero_rg="9999/2026",
            data_udienza=date(2026, 3, 20),
            attivita_richieste="Test form submission"
        )
        
        # Simulo salvataggio file come fa la view
        for f in [file1, file2]:
            DomiciliazioniDocument.objects.create(
                submission=submission,
                file=f,
                original_filename=f.name
            )
        
        self.assertEqual(submission.documents.count(), 2)
        
        # Verifico i nomi con spazi
        filenames = list(submission.documents.values_list('original_filename', flat=True))
        self.assertIn("allegato 1.pdf", filenames)
        self.assertIn("documento test 2.pdf", filenames)
