# **Personal Finance Tracker**  

## **Overview**  
Personal Finance Tracker is a web application that helps users manage their income and expenses efficiently. It provides interactive data visualizations, budget management, and historical transaction tracking to enhance financial decision-making.  

## **Features**  
- **User Authentication**: Secure registration and login system.  
- **Income & Expense Management**: Add, edit, and categorize transactions.  
- **Budget Tracking**: Set monthly budgets and receive notifications for overspending.  
- **Transaction History**: Filter and export financial records.  
- **Account Management**: Track multiple accounts and transfer funds.  
- **Data Visualization**: Interactive charts for financial insights.  

## **Technology Stack**  
- **Backend**: Django, Python  
- **Frontend**: HTML, CSS, JavaScript, AJAX  
- **Database**: SQLite (supports PostgreSQL/MySQL migration)  
- **Visualization**: Chart.js  
- **Task Queue**: Celery + Redis  

## **Installation**  
1. Clone the repository:  
   ```bash
   git clone <repository-url>
   cd personal-finance-tracker
   ```
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:  
   ```bash
   python manage.py migrate
   ```
4. Start the server:  
   ```bash
   python manage.py runserver
   ```
5. Access the application.

