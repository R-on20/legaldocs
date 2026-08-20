# AI Search Setup for Django Legal Document Management System

## Installation

1. Install the OpenAI Python library:
```bash
pip install openai
```

2. Get your OpenAI API key:
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key (it starts with "sk-")

3. Update your Django settings.py:
   - Replace 'your-openai-api-key-here' with your actual API key
   - Set AI_SEARCH_ENABLED = True

## Configuration Options

In your settings.py, you can configure:

```python
# OpenAI Configuration
OPENAI_API_KEY = 'sk-your-actual-key-here'  # Your OpenAI API key
OPENAI_MODEL = 'gpt-3.5-turbo'  # or 'gpt-4' if you have access
AI_SEARCH_ENABLED = True  # Set to False to disable AI search

# Optional: Configure AI search behavior
AI_SEARCH_FALLBACK = True  # Whether to fallback to keyword search on AI failure
AI_SEARCH_MAX_TOKENS = 500  # Maximum tokens for AI response
AI_SEARCH_TEMPERATURE = 0.1  # Lower = more consistent, higher = more creative
```

## Example Queries

The AI search can understand natural language queries like:

### Document Type Queries
- "Show me all contracts"
- "Find legal notices from this year"
- "Water supply agreements"

### Date-based Queries
- "Documents uploaded last month"
- "Contracts from this year"
- "Files uploaded last week"

### Status and Content Queries
- "Approved documents about water rights"
- "Draft contracts"
- "Confidential documents"

### Complex Queries
- "Show me contracts uploaded by john last month about water supply"
- "Find all confidential legal notices from this year"
- "Draft agreements about service contracts"

## How It Works

1. **Query Processing**: User enters natural language query
2. **AI Analysis**: OpenAI GPT analyzes the query and extracts:
   - Document types (CONTRACT, LEGAL_NOTICE, etc.)
   - Date ranges (last week, this month, specific dates)
   - Status filters (DRAFT, APPROVED, etc.)
   - Keywords for content search
   - Other metadata filters

3. **Filter Application**: Extracted filters are applied to Django QuerySet
4. **Fallback**: If AI fails, system falls back to keyword search
5. **Results Display**: Shows results with AI analysis details

## Troubleshooting

### AI Search Not Working
1. Check your API key is correct
2. Ensure you have OpenAI credits
3. Check the logs for error messages
4. Verify AI_SEARCH_ENABLED = True

### Fallback to Keyword Search
This is normal behavior when:
- OpenAI API is unavailable
- API key is missing or invalid
- Query parsing fails
- Network issues occur

### Rate Limiting
If you hit rate limits:
- Upgrade your OpenAI plan
- Implement caching for common queries
- Add delays between requests

## Customization

### Modify the AI Prompt
Edit the prompt in `documents/ai_search.py` in the `_call_openai_api` method to:
- Add more document types
- Include custom fields
- Change the response format
- Add legal-specific instructions

### Add Custom Filters
Extend the `_validate_filters` method to support:
- Custom metadata fields
- Legal practice areas
- Client-specific filters
- Matter numbers

### Frontend Customization
Modify the template to:
- Change the AI badge appearance
- Add more filter displays
- Customize the analysis details
- Add search suggestions

## Cost Considerations

- GPT-3.5-turbo: ~$0.002 per 1K tokens (very affordable)
- GPT-4: ~$0.03 per 1K tokens (more expensive but better)
- Average query cost: $0.001-0.01 per search
- Consider caching for repeated queries

## Security Notes

- Never commit API keys to version control
- Use environment variables for production
- Implement rate limiting for public-facing searches
- Consider user authentication for AI features
- Monitor API usage and costs
