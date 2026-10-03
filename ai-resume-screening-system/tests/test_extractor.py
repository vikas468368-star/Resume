import os
import unittest
import docx
from app.services.extractor import clean_extracted_text, extract_resume_text

class ExtractorTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_uploads')
        os.makedirs(self.test_dir, exist_ok=True)

    def test_text_cleaning_and_normalization(self):
        dirty_text = "\xa0John   Doe\n\n\n\n\uf0b7 Python Developer\u2013Full Stack\t\t\n   Experienced   with SQL   \n\n\n\n"
        cleaned = clean_extracted_text(dirty_text)
        
        self.assertNotIn('\xa0', cleaned)
        self.assertNotIn('\uf0b7', cleaned)
        self.assertIn('- Python Developer-Full Stack', cleaned)
        self.assertIn('Experienced with SQL', cleaned)
        # Check no more than 2 consecutive blank lines
        self.assertNotIn('\n\n\n', cleaned)

    def test_docx_extraction(self):
        docx_path = os.path.join(self.test_dir, 'sample_test_resume.docx')
        doc = docx.Document()
        doc.add_heading('Samantha Hayes', 0)
        doc.add_paragraph('Email: samantha.hayes@example.com | Phone: (555) 123-4567')
        doc.add_paragraph('Experienced Python and Flask Engineer with 4 years in software development.')
        
        table = doc.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Skill"
        table.rows[0].cells[1].text = "Level"
        table.rows[1].cells[0].text = "PostgreSQL"
        table.rows[1].cells[1].text = "Expert"
        
        doc.save(docx_path)

        extracted = extract_resume_text(docx_path)
        self.assertIn("Samantha Hayes", extracted)
        self.assertIn("samantha.hayes@example.com", extracted)
        self.assertIn("Python and Flask", extracted)
        self.assertIn("PostgreSQL", extracted)

    def test_unsupported_file_format_raises_error(self):
        fake_file = os.path.join(self.test_dir, 'invalid_format.xyz')
        with open(fake_file, 'w') as f:
            f.write("Some random text")
            
        with self.assertRaises(ValueError):
            extract_resume_text(fake_file)

if __name__ == '__main__':
    unittest.main()
