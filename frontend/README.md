# Compliance Auditor Frontend

A modern React frontend for the Compliance Auditor tool that scans Git repositories for compliance issues, security vulnerabilities, and best practice violations.

## Features

- **Repository Scanning**: Scan GitHub, GitLab, and Bitbucket repositories
- **Compliance Dashboard**: Overview of scan results and statistics
- **Detailed Results**: View comprehensive scan results with issue details
- **Scan History**: Track and review previous scans
- **Compliance Rules**: View and understand the compliance rules being applied
- **Modern UI**: Beautiful, responsive design with smooth animations
- **Real-time Updates**: Live scanning progress and results
- **Export Functionality**: Export scan results as JSON

## Technology Stack

- **React 18** - Modern React with hooks and context
- **React Router** - Client-side routing
- **Styled Components** - CSS-in-JS styling
- **Axios** - HTTP client for API communication
- **React Icons** - Beautiful icon library
- **React Toastify** - Elegant notifications
- **Date-fns** - Date manipulation and formatting

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

### Building for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.js     # Main dashboard
│   ├── Navbar.js        # Navigation bar
│   ├── RepositoryScanner.js  # Repository scanning form
│   ├── ScanResults.js   # Scan results display
│   ├── ScanHistory.js   # Scan history list
│   └── ComplianceRules.js    # Compliance rules overview
├── context/             # React context for state management
│   └── AppContext.js    # Global application state
├── services/            # API service layer
│   └── api.js          # Axios configuration and API calls
├── utils/              # Utility functions
│   └── helpers.js      # Helper functions
├── config/             # Configuration files
│   └── constants.js    # Application constants
├── App.js              # Main App component
├── index.js            # Application entry point
└── index.css           # Global styles
```

## Features Overview

### Dashboard
- **Statistics Cards**: Total scans, successful scans, issues found, API status
- **Quick Actions**: Direct links to scanner, history, and rules
- **Recent Activity**: Overview of recent scan activity

### Repository Scanner
- **URL Input**: Support for HTTPS and SSH Git URLs
- **Provider Selection**: GitHub, GitLab, Bitbucket
- **Advanced Options**: Branch selection, analysis depth
- **Example URLs**: Click-to-fill example repository URLs
- **Real-time Validation**: URL format validation

### Scan Results
- **Status Overview**: Success/failure status with details
- **Repository Info**: Branch, author, commit details, scan duration
- **Statistics**: File count, issues found, total commits
- **Issue Details**: Detailed list of compliance issues found
- **File Listing**: Repository files scanned
- **Export Options**: Download results as JSON, share results

### Scan History
- **Search & Filter**: Search by repository name, filter by status
- **Detailed Listings**: Repository details, scan statistics, timestamps
- **Quick Actions**: View results, export individual scans
- **Status Indicators**: Visual status badges for each scan

### Compliance Rules
- **Rule Categories**: Security, Legal, Quality, Privacy, Documentation
- **Rule Details**: Description, patterns, file types, severity
- **Status Indicators**: Active/inactive rules
- **Statistics**: Total rules, active rules, severity breakdown

## API Integration

The frontend integrates with the FastAPI backend through these endpoints:

- `GET /` - API information
- `GET /health` - Health check
- `GET /git-scan` - Simple repository scan
- `POST /git-scan-detailed` - Detailed repository scan
- `GET /scan-history` - Scan history
- `GET /compliance-rules` - Compliance rules

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

### API Configuration

The API base URL can be configured in `src/services/api.js`:

```javascript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
});
```

## State Management

The application uses React Context for state management:

- **AppContext**: Global application state
- **Actions**: State update functions
- **Reducers**: State transformation logic

### Key State Properties

- `scanResults`: Array of scan results
- `currentScan`: Currently active scan
- `isLoading`: Loading state indicator
- `error`: Error state
- `scanHistory`: Historical scan data
- `complianceRules`: Available compliance rules
- `apiStatus`: Backend API status

## Styling

The application uses a combination of:

- **Styled Components**: Component-specific styles
- **Global CSS**: Base styles and utilities
- **Design System**: Consistent colors, typography, and spacing

### Theme Colors

- Primary: `#3b82f6` (Blue)
- Secondary: `#64748b` (Slate)
- Success: `#22c55e` (Green)
- Warning: `#f59e0b` (Amber)
- Error: `#dc2626` (Red)

## Responsive Design

The application is fully responsive with breakpoints:

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Code Style

- Use functional components with hooks
- Follow React best practices
- Use meaningful component and variable names
- Add comments for complex logic
- Keep components focused and reusable

## Deployment

### Build

```bash
npm run build
```

### Deploy to Static Hosting

The build folder can be deployed to any static hosting service:

- Netlify
- Vercel
- GitHub Pages
- AWS S3
- Azure Static Web Apps

### Environment Configuration

For production deployment, configure the API URL:

```env
REACT_APP_API_URL=https://your-api-domain.com
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:

- Check the backend API documentation
- Review the component documentation
- Check browser console for errors
- Ensure the backend API is running and accessible
