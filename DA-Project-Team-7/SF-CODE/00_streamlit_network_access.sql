USE ROLE ACCOUNTADMIN;

-- Step 1: define which internet addresses are allowed (just PyPI, the Python package repository)
CREATE OR REPLACE NETWORK RULE pypi_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org', 'files.pythonhosted.org');

-- Step 2: wrap that rule into an "integration" object the Streamlit app can use
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
  ALLOWED_NETWORK_RULES = (pypi_network_rule)
  ENABLED = TRUE;