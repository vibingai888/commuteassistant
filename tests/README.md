# Test Suite Documentation

This directory contains comprehensive unit tests and integration tests for the Podcast Generator API.

## Test Structure

```
tests/
├── __init__.py                 # Makes tests a Python package
├── test_config.py             # Configuration module tests
├── test_models.py             # Pydantic models tests
├── test_utils.py              # Utility functions tests
├── test_script_service.py     # Script generation service tests
├── test_tts_service.py        # TTS service tests
├── test_api_endpoints.py      # API endpoint tests
├── test_integration.py        # Integration tests
└── README.md                  # This file
```

## Test Categories

### 1. Unit Tests (`test_config.py`, `test_models.py`, `test_utils.py`)
- **Purpose**: Test individual functions and classes in isolation
- **Coverage**: Configuration validation, model validation, utility functions
- **Mocking**: External dependencies are mocked
- **Speed**: Fast execution

### 2. Service Tests (`test_script_service.py`, `test_tts_service.py`)
- **Purpose**: Test business logic services
- **Coverage**: Script generation, TTS generation, error handling
- **Mocking**: External APIs (Google Gemini) are mocked
- **Speed**: Medium execution

### 3. API Tests (`test_api_endpoints.py`)
- **Purpose**: Test HTTP endpoints and request/response handling
- **Coverage**: All API endpoints, validation, error responses
- **Mocking**: Internal services are mocked
- **Speed**: Fast execution

### 4. Integration Tests (`test_integration.py`)
- **Purpose**: Test complete workflows and system integration
- **Coverage**: End-to-end podcast generation flow
- **Mocking**: External APIs only
- **Speed**: Medium execution

## Running Tests

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="test-api-key"
export GOOGLE_CLOUD_PROJECT="test-project"
```

### Running All Tests
```bash
# Using the test runner script
./run_tests.sh

# Using pytest directly
pytest tests/ -v
```

### Running Specific Test Categories
```bash
# Unit tests only
pytest tests/ -m "unit" -v

# Integration tests only
pytest tests/ -m "integration" -v

# API tests only
pytest tests/ -m "api" -v
```

### Running Specific Test Files
```bash
# Run configuration tests
pytest tests/test_config.py -v

# Run model tests
pytest tests/test_models.py -v

# Run utility tests
pytest tests/test_utils.py -v
```

### Running Specific Test Functions
```bash
# Run a specific test function
pytest tests/test_config.py::TestConfig::test_default_values -v

# Run all tests in a specific class
pytest tests/test_models.py::TestPodcastRequest -v
```

### Running with Coverage
```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## Test Coverage

### Configuration Tests (`test_config.py`)
- ✅ Default configuration values
- ✅ Environment variable loading
- ✅ Configuration validation
- ✅ Error handling for missing required variables
- ✅ Type conversions (string to int, string to bool)

### Model Tests (`test_models.py`)
- ✅ Valid request/response validation
- ✅ Invalid data rejection
- ✅ CamelCase/snake_case field mapping
- ✅ Required field validation
- ✅ Data type validation
- ✅ Range validation (minutes, word counts)

### Utility Tests (`test_utils.py`)
- ✅ WAV file creation from PCM data
- ✅ Base64 encoding/decoding
- ✅ Audio duration calculation
- ✅ Duration formatting
- ✅ Error handling for invalid data

### Script Service Tests (`test_script_service.py`)
- ✅ Word counting functionality
- ✅ JSON string cleaning
- ✅ Script validation
- ✅ Turn chunking logic
- ✅ Script generation with mocked API
- ✅ Error handling for API failures
- ✅ Input validation

### TTS Service Tests (`test_tts_service.py`)
- ✅ TTS generation with valid input
- ✅ Audio format conversion (PCM to WAV)
- ✅ Base64 data handling
- ✅ Error handling for various failure scenarios
- ✅ Conversation text building
- ✅ Response validation

### API Endpoint Tests (`test_api_endpoints.py`)
- ✅ Health check endpoint
- ✅ Suggestions endpoint
- ✅ Script generation endpoint
- ✅ TTS segment endpoint
- ✅ CORS headers
- ✅ API documentation accessibility
- ✅ Error responses
- ✅ Request validation

### Integration Tests (`test_integration.py`)
- ✅ Complete podcast generation flow
- ✅ End-to-end script to TTS pipeline
- ✅ Error handling and recovery
- ✅ API documentation verification
- ✅ CORS functionality
- ✅ Suggestions endpoint integration

## Test Data

### Mock Responses
Tests use realistic mock responses that simulate actual API behavior:

```python
# Example script generation mock
mock_script_response.text = '''
{
    "segments": [
        {
            "segmentId": 1,
            "multiSpeakerMarkup": {
                "turns": [
                    {"text": "Hello, welcome to our podcast!", "speaker": "Jay"},
                    {"text": "Thanks for having me!", "speaker": "Nik"}
                ]
            }
        }
    ],
    "total_words": 15
}
'''
```

### Test Audio Data
```python
# Example TTS mock
mock_tts_inline_data.mime_type = "audio/wav"
mock_tts_inline_data.data = base64.b64encode(b"fake_audio_data").decode('utf-8')
```

## Continuous Integration

### GitHub Actions
The `.github/workflows/tests.yml` file defines CI/CD pipeline that:
- Runs on every push and pull request
- Tests against Python 3.11 and 3.12
- Generates coverage reports
- Runs linting checks
- Uploads coverage to Codecov

### Local Development
```bash
# Run tests before committing
./run_tests.sh

# Run specific tests during development
pytest tests/test_script_service.py -v -s

# Run tests with detailed output
pytest tests/ -v -s --tb=long
```

## Best Practices

### Writing New Tests
1. **Follow naming convention**: `test_*.py` files, `Test*` classes, `test_*` functions
2. **Use descriptive test names**: `test_script_generation_with_invalid_topic`
3. **Test both success and failure cases**
4. **Mock external dependencies**
5. **Use fixtures for common setup**
6. **Add appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`

### Test Organization
```python
class TestFeatureName:
    """Test cases for feature description"""
    
    def test_success_scenario(self):
        """Test successful operation"""
        # Arrange
        # Act
        # Assert
    
    def test_error_scenario(self):
        """Test error handling"""
        # Arrange
        # Act & Assert
        with pytest.raises(ExpectedException):
            function_call()
```

### Mocking Guidelines
```python
@patch('module.function_name')
def test_with_mock(self, mock_function):
    # Setup mock
    mock_function.return_value = expected_value
    
    # Call function
    result = function_under_test()
    
    # Assert
    assert result == expected_value
    mock_function.assert_called_once()
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the `cursor` directory
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Environment Variables**: Set `GOOGLE_API_KEY` and `GOOGLE_CLOUD_PROJECT`
4. **Mock Issues**: Check that mock paths match actual import paths

### Debugging Tests
```bash
# Run with debug output
pytest tests/ -v -s --tb=long

# Run single test with debugger
pytest tests/test_config.py::TestConfig::test_default_values -v -s

# Run with print statements
pytest tests/ -v -s --capture=no
```

## Performance

### Test Execution Times
- **Unit Tests**: < 1 second
- **Service Tests**: 1-2 seconds
- **API Tests**: 1-2 seconds
- **Integration Tests**: 2-5 seconds
- **Full Test Suite**: 5-10 seconds

### Optimization Tips
1. Use `@pytest.fixture(scope="session")` for expensive setup
2. Mock external API calls
3. Use `pytest-xdist` for parallel execution
4. Cache test data when possible

## Coverage Goals

- **Target Coverage**: > 90%
- **Critical Paths**: 100%
- **Error Handling**: 100%
- **API Endpoints**: 100%

Current coverage can be viewed by running:
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

