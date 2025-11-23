# Bot de Discord + Dashboard Web - Información del Proyecto

## Overview
This project is a comprehensive, professional system for managing gaming tournaments on Discord. It features a dual interface: an interactive Discord Bot (Python) with buttons, modals, and slash commands, and a Web Dashboard (Node.js/Express) for remote administration using OAuth2. Key capabilities include data persistence via JSON files, automatic role management, scheduled room management, and a global ranking system. The business vision is to provide a robust, interactive, and user-friendly platform for organizing and tracking gaming tournaments, appealing to competitive gaming communities and enhancing their organizational capabilities.

## User Preferences
- Idioma: Español
- Tipo de proyecto: Bot de Discord para gestión de torneos gaming
- Enfoque: Sistema profesional e interactivo con persistencia de datos
- UI: Botones y modales para mejor experiencia de usuario

## System Architecture

### Core Architecture
The system is divided into two main components: a Discord Bot built with Python (discord.py) and a Web Dashboard using Node.js/Express. Data persistence is managed through JSON files, shared between both components. Authentication for the web dashboard utilizes Discord OAuth2. The UI for the bot is interactive, leveraging Discord's native UI elements (buttons, modals, select menus), while the web dashboard uses EJS templates and responsive CSS for a modern, MEE6-style interface.

### UI/UX Decisions
The aesthetic theme is an "Elegante Estética Oscura" (Elegant Dark Aesthetic).
- **Color Palette**: Predominantly dark backgrounds (#0A0D12, #131820, #1A1F2E), with deep blues and greens as accents (#1E2A47, #182A3A, #3D5A80). Text colors are soft whites and grays (#F5F5F5, #E4E4E4).
- **Design Elements**: Subtle Glassmorphism (60% opacity, 12px blur), no harsh glows, soft contrasts.
- **Typography**: Clean, using Inter for body text and Poppins for titles.
- **Shapes**: Rounded borders (12-20px) for a modern look.
- **Effects**: Soft shadows, smooth 0.2s transitions for interactions, fade-in animations (0.4-0.5s) on module load, subtle hover effects.
- **Responsive Design**: Full responsive grid for mobile, tablet, and desktop.

### Technical Implementations & Feature Specifications
**Discord Bot:**
- Interactive dashboard with dynamic embeds, real-time updates, and persistent messages.
- Advanced tournament system: creation, team registration, team switching, automatic role assignment, and tournament finalization.
- Global ranking: tracks team victories, displays top 10, and includes a `/ranking` slash command.
- Room/Sala management: timed room creation (open/close), join verification, automatic "Jugador" role, automatic closing with reminders.
- Utility commands: scrim announcements, polls, random team generator, help system.
- Modals for various user and admin actions (e.g., `UnirseModal`, `CrearTorneoModal`, `CrearSalaModal`).
- Private Admin Panel with specific functions for managing tournaments and rooms.
- Notification system for rooms including activation/deactivation, role notification, custom messages, and DM automation.

**Web Dashboard:**
- Secure Discord OAuth2 authentication.
- Exclusive admin panel for remote control.
- Management of rooms, announcements, and activity logs.
- Responsive and modern interface following a MEE6-style professional dashboard.
- REST API for bot control and data integration.
- Supports multiple servers.
- Visual server selector and intuitive sidebar navigation.

### System Design Choices
- **Data Persistence**: JSON files are used (`torneos.json`, `ranking.json`, `salas.json`, `config.json`) for shared data between bot and web. The web dashboard also uses `salas.json`, `settings.json`, and `logs.json` in its `database` folder.
- **Environment Configuration**: Utilizes environment variables for sensitive data like `DISCORD_TOKEN`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `GUILD_ID`, `ADMIN_ROLE_IDS`, and `SESSION_SECRET`.
- **Discord Intents & Permissions**: Requires `intents.members = True` and `intents.message_content = True`, along with specific Discord permissions (Send Messages, Manage Messages, Manage Channels, Manage Roles, Read Message History, Add Reactions, Use Application Commands).
- **Security**: Bot token in Replit Secrets, admin permission validation, secure OAuth2, encrypted sessions, sensitive data in environment variables, and activity logging.

## External Dependencies

- **Discord API**: Core integration for both the Python Bot (via `discord.py`) and the Node.js Web Dashboard (for OAuth2 authentication and API interactions).
- **Node.js/Express**: Backend framework for the Web Dashboard.
- **EJS Templates**: Used for rendering dynamic HTML in the Web Dashboard.
- **JSON Files**: Used for data persistence across both bot and web components.