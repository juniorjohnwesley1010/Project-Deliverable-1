import unittest
from customos.parser import parse_command, ParseError


class ParserTests(unittest.TestCase):
    def test_normal_args(self):
        self.assertEqual(parse_command('echo "hello world"'), (["echo", "hello world"], False))

    def test_background_with_no_spaces(self):
        self.assertEqual(parse_command('sleep 5&'), (["sleep", "5"], True))

    def test_blank(self):
        self.assertEqual(parse_command('   '), ([], False))

    def test_unterminated_quote(self):
        with self.assertRaises(ParseError):
            parse_command('echo "unterminated')

    def test_reject_pipe_until_deliverable_four(self):
        with self.assertRaises(ParseError):
            parse_command('ls | grep sample')

    def test_reject_invalid_background(self):
        with self.assertRaises(ParseError):
            parse_command('echo & test')


if __name__ == '__main__':
    unittest.main()
