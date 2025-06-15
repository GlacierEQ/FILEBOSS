import unittest
from unittest.mock import Mock
from calendar_manager import CalendarManager
from communication_handler import CommunicationHandler
from research_enhancer import ResearchEnhancer

class TestCoreInfrastructure(unittest.TestCase):
    def test_calendar_creation(self):
        mock_creds = Mock()
        calendar = CalendarManager(mock_creds)
        self.assertIsNotNone(calendar.service)
        
    def test_communication_handler_init(self):
        comm = CommunicationHandler('twilio_sid', 'twilio_token', 'user@law.com', 'pass123')
        self.assertIsNotNone(comm.twilio)
        self.assertIsNotNone(comm.email_user)
        
    def test_research_validation(self):
        research = ResearchEnhancer('http://legal-db/api')
        self.assertTrue(research.validate_citation('123 US 456'))
        self.assertFalse(research.validate_citation('invalid_citation'))

if __name__ == '__main__':
    unittest.main()
