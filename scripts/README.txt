RESEARCH INTELLIGENCE ENGINE — FILE-BASED WORKFLOW

Copy ship.ps1 into:
C:\Users\Admin\Documents\ResearchIntelligence\scripts\ship.ps1

Then, from the ResearchIntelligence project root, run:

.\scripts\ship.ps1 "Describe the change"

The script:
1. runs pytest;
2. stops on test failure;
3. stages changes;
4. commits;
5. pushes to GitHub.

Do not store secrets, API keys, tokens, passwords, or private data in the public repository.
