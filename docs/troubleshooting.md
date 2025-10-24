# Troubleshooting

## Common Issues

### "No data was processed" Error

If you encounter the "No data was processed. No results to display." error, this typically indicates one of the following issues:

1. **API Response Format Changes**: The CalypsoAI API response format has been updated. The evaluator now handles the new format automatically, but if you're still seeing this error, check that your API credentials are correct.

2. **Dataset Format Issues**: Ensure your input CSV file follows the correct format:
   ```
   "prompt text"|expected_result
   ```
   The expected result should be "true" or "false" without extra quotes.

3. **Environment Variables**: Verify that your `.env` file contains the correct API credentials:
   ```
   CALYPSOAI_URL=https://calypsoai.app
   CALYPSOAI_TOKEN=your_api_token_here
   ```

4. **API Connectivity**: Check that you can reach the CalypsoAI API and that your token is valid.

### Quick Fix for Existing Results

If you have existing scan results in CSV format, you can use the `evaluate_existing_results.py` script to calculate accuracy metrics without re-scanning:

```bash
python evaluate_existing_results.py --input your_existing_results.csv
```

This bypasses the API scanning step and directly calculates accuracy from your existing data.

## Error Handling

The evaluators include robust error handling for common issues:

- File not found errors
- Empty datasets
- API errors
- Invalid file formats

When errors occur, the evaluators will display helpful error messages and exit gracefully.

## Platform-Specific Issues

### CalypsoAI Issues

- **Scanner Configuration**: Ensure only relevant scanners are enabled in your CalypsoAI platform
- **API Rate Limits**: If you encounter rate limiting, consider processing smaller batches
- **Token Expiration**: Check that your API token is valid and not expired


## Getting Help

If you continue to experience issues:

1. Check the error messages carefully - they often contain specific guidance
2. Verify your environment variables are set correctly
3. Test with a small dataset first
4. Check the API documentation for any recent changes
5. Review the sample datasets to ensure your input format is correct

## Validation

To verify your setup is working correctly, run:

```bash
python validate_setup.py
```

This will check:
- Python dependencies
- Environment variables
- API connectivity (if credentials are provided)
- File permissions
