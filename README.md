# telecaller_minor
📞 Telecaller Management & Routing System
A robust, multi-threaded Python application designed to simulate a high-traffic call center environment. This system manages employee lifecycles, intelligent call routing based on priority, and persistent performance analytics.

🌟 Key Features
1. Intelligent Priority Routing
The system uses a "Waterfall Search" logic to ensure customers are handled by the appropriate rank:

VVIP (Priority 1): Routed directly to Directors.

VIP (Priority 2): Routed to Managers.

General (Priority 3): Handled by Respondents.

Fallback: If the preferred rank is busy, the system automatically searches for any available agent across other ranks.

2. Automated Escalation Logic
Includes a post-call satisfaction check. If a customer is marked as "Unsatisfied," the system automatically escalates their priority level and places them at the front of the queue for a higher-ranking official.

3. Concurrency & Thread Safety
Built using the threading module to allow:

Simultaneous call handling (multiple calls happening at once).

Non-blocking background processes for user feedback.

Thread Locking: Utilizes data_lock and status_lock to prevent data corruption during simultaneous access.

4. Persistent Data Analytics
JSON Storage: All employee performance data is saved permanently to a JSON file.

Time-Based Bifurcation: Generates on-the-fly reports for call volume categorized by Today, Last 7 Days, Last 30 Days, and Total.

🛠️ Technical Stack
Language: Python 3.x

Concurrency: threading (Multi-threading & Timer objects)

Data Format: JSON (Persistent storage)

Monitoring: logging (Audit trail of all system events)

Time Management: datetime & timedelta

🚀 How to Use
Configure: Edit config.json to set your desired call durations and queue limits.

Add Staff: Use the menu to register Directors, Managers, and Respondents.

Process Calls: Input incoming calls and watch the system route them based on live agent availability.

Analyze: View the Full Performance Report to track agent efficiency over time.

📂 Project Structure
main.py: The core application logic.

config.json: External configuration for system parameters.

call_centre.data.json: The local database for persistent stats.

call_center.log: Auto-generated audit trail for debugging.
