# Personal Gmail Agent

An intelligent Gmail management system built with Google's ADK (Agent Development Kit) that provides comprehensive email assistance through specialized sub-agents.

## 🌟 Features

### Intelligent Agent Delegation System
The system automatically routes queries to specialized sub-agents based on context and keywords:

- **🕐 Time Intelligence Agent** - Handles all date/time-related queries
- **📊 Content Analysis Agent** - Email summarization and content extraction  
- **🔍 Search & Filtering Agent** - Advanced search with intelligent sender resolution
- **📁 Organization Agent** - Label management and mailbox organization
- **⚡ Priority & Triage Agent** - Email importance assessment and prioritization
- **📈 Digest & Reporting Agent** - Email analytics and periodic summaries
- **🛡️ Security Monitoring Agent** - Threat detection and security analysis

### Key Capabilities

- **Smart Sender Resolution**: Automatically handles fuzzy matching for senders (e.g., "Interview Query" → finds related newsletters and content)
- **Time-Aware Operations**: Natural language time processing ("last week", "today", "recent emails")
- **Content Intelligence**: Automatic action item extraction, priority assessment, and content summarization
- **Security Monitoring**: Phishing detection and suspicious email identification
- **Label Management**: Comprehensive label analysis and organization insights
- **Intelligent Search**: Multi-pattern search with confidence scoring and suggestions

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Gmail API credentials from Google Cloud Console
- Gmail account with API access enabled

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nil1729/personal-agent-google-adk
cd personal-agent-google-adk
```

2. Install dependencies:
```bash
uv sync --frozen
```

3. Set up Gmail API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create credentials (OAuth 2.0 Client IDs)
   - Download the credentials JSON file

4. Set environment variables:
```bash
export GMAIL_APP_CREDENTIALS_FILE="path/to/your/credentials.json"
export GMAIL_APP_TOKEN_FILE="gmail_token.json"  # Optional, defaults to gmail_token.json
```

### First Run



### First Run

1. Start the ADK web interface:
```bash
adk web
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. You'll see the Gmail Manager agent interface where you can chat directly with the system using natural language.

4. On first run, you'll be guided through the Gmail OAuth authentication flow to connect your account.

The agent will automatically understand your requests and delegate them to the appropriate specialized sub-agents based on context and keywords.

## 🏗️ Architecture

### Root Agent
The main `gmail_manager` agent coordinates all operations and intelligently delegates queries to specialized sub-agents based on keywords and context.

### Sub-Agents

#### Time Intelligence Agent (`time_intelligence`)
- Processes relative time expressions ("last 3 days", "this week")
- Calculates exact date ranges from natural language
- Handles time-aware email operations

#### Content Analysis Agent (`content_analyzer`)
- Email summarization and thread analysis
- Action item and deadline extraction
- Contact and event identification
- Sentiment and priority analysis

#### Search & Filtering Agent (`search_specialist`)
- Multi-pattern search strategies
- Intelligent sender resolution with fuzzy matching
- Confidence scoring for search results
- Search optimization and suggestions

#### Organization Agent (`label_organizer`)
- Label management and statistics
- Mailbox organization insights
- Label optimization recommendations
- Email categorization analysis

#### Priority & Triage Agent (`priority_manager`)
- Automatic importance assessment
- VIP sender detection
- Urgent email identification
- Inbox triage and focus management

#### Digest & Reporting Agent (`digest_generator`)
- Daily/weekly email summaries
- Email analytics and trends
- Activity reports and insights
- Productivity pattern analysis

#### Security Monitoring Agent (`security_monitor`)
- Phishing and threat detection
- Suspicious sender identification
- Security recommendations
- Privacy and data protection monitoring

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_APP_CREDENTIALS_FILE` | Path to Gmail API credentials JSON | Required |
| `GMAIL_APP_TOKEN_FILE` | Path to store OAuth token | `gmail_token.json` |

### Gmail API Scopes

The application uses read-only Gmail access:
- `https://www.googleapis.com/auth/gmail.readonly`

## 🛠️ Development

### Project Structure
```
personal-agent/
├── app/
│   ├── agent.py              # Root agent with delegation logic
│   ├── clients/
│   │   └── gmail.py          # Gmail API client
│   ├── sub_agents/
│   │   └── gmail/            # Specialized sub-agents
│   │       ├── time_intelligence.py
│   │       ├── content_analysis.py
│   │       ├── search_filtering.py
│   │       ├── organization.py
│   │       ├── priority_triage.py
│   │       ├── digest_reporting.py
│   │       └── security_monitoring.py
│   └── tools/
│       └── gmail.py          # Gmail utility functions
├── pyproject.toml
└── README.md
```

### Key Components

#### Gmail Client (`app/clients/gmail.py`)
- Handles OAuth authentication
- Maintains Gmail service connection
- Provides secure credential management

#### Gmail Tools (`app/tools/gmail.py`)
- 20+ specialized functions for email operations
- Label management and statistics
- Time-aware search and filtering
- Email content extraction and parsing

#### Agent System
- Root agent with intelligent delegation
- 7 specialized sub-agents with distinct capabilities
- Automatic query routing and result coordination

## 🔒 Security & Privacy

- **Read-Only Access**: Uses Gmail read-only scopes for maximum security
- **Local Processing**: All analysis happens locally, no data sent to third parties
- **Secure Authentication**: OAuth 2.0 flow with token refresh handling
- **Threat Detection**: Built-in security monitoring for suspicious emails

## 📊 Advanced Features

### Intelligent Sender Resolution
When you search for senders that don't match exactly:
1. Tries multiple search approaches automatically
2. Uses fuzzy matching for company names and people
3. Searches by content when direct sender match fails
4. Provides confidence scores for suggested matches
5. Groups related results with explanations

### Multi-Agent Coordination
Complex queries automatically coordinate multiple agents:
- Primary agent handles main query aspect
- Supporting agents provide supplementary information
- Results are synthesized into coherent responses

### Proactive Intelligence
- Suggests related actions after completing requests
- Provides context-aware recommendations
- Surfaces relevant insights automatically
- Guides users toward efficient email workflows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the existing issues in the GitHub repository
2. Create a new issue with detailed information
3. Include error messages and configuration details

## 🙏 Acknowledgments

- Built with Google's Agent Development Kit (ADK)
- Uses Gmail API for secure email access
- Powered by Gemini 2.5 Flash model for intelligent processing
