# Suggestions Feature - Setup & Usage Guide

## What Was Fixed

1. **Modal Display** - Updated JavaScript to properly show/hide the suggestion modal with `display: flex/none` instead of using Tailwind's `hidden` class
2. **Form Validation** - Added client-side validation to ensure all fields are filled before submission
3. **Error Handling** - Fixed backend error responses to include all required template variables
4. **Email in Session** - Email is now stored during login and pre-fills in the form
5. **Escape Key Support** - Modal can now be closed by pressing Escape
6. **Body Overflow** - Prevents body scrolling when modal is open

## How to Use

### For Regular Users

1. **Log in** to your account
2. Click **Suggestions** in the navbar
3. Click the green **Submit Suggestion** button
4. A modal form will appear with these fields:
   - **Email Address** (auto-filled from your login)
   - **SDG Category** (dropdown with all 17 SDGs)
   - **Suggestion Title** (brief summary)
   - **Description** (detailed explanation)
5. Click **Submit Suggestion** to submit
6. You'll see a success message confirming submission
7. Your suggestion will appear in the "Pending" list

### For Admins

1. Go to **Suggestions** page
2. Click filter buttons to view:
   - All Suggestions
   - Pending (yellow)
   - Approved (green)
   - Rejected (red)
3. Click the dropdown next to each suggestion to change status:
   - Pending → Approved → Reject
4. Status changes are saved instantly
5. Admin actions are logged to Recent Activity

## Starting the Application

```powershell
cd "C:\Users\Cess\Documents\Final Project"
& ".venv\Scripts\python.exe" "app.py"
```

Then visit: http://127.0.0.1:5000

## Database Schema

The `suggestions` table stores:
- `id` - Unique suggestion ID
- `user_id` - ID of user who submitted
- `fullname` - User's full name
- `email` - User's email
- `sdg_category` - One of 17 SDG categories
- `title` - Suggestion title
- `description` - Detailed description
- `status` - pending/approved/rejected
- `created_at` - Timestamp of submission

## Troubleshooting

### Modal doesn't appear
- Check browser console (F12) for JavaScript errors
- Ensure you're logged in
- Try clearing browser cache

### Form submission fails
- Verify all fields are filled (including email)
- Check that email field is not empty
- Look at browser console for errors

### Suggestions don't save
- Check app.py console for database errors
- Verify suggestions table exists: `SELECT COUNT(*) FROM suggestions;`
- Check database permissions

### Admin status updates not working
- Verify you're logged in as an admin (role = 'admin')
- Check browser console for errors
- Try refreshing the page

## Files Modified

- `app.py` - Added `/suggestions`, `/submit-suggestion`, `/update-suggestion` routes
- `templates/suggestions.html` - Full suggestions page with modal and form
- `templates/dashboard.html` - Added Suggestions nav link
- `templates/statistics.html` - Added Suggestions nav link  
- `templates/manage.html` - Added Suggestions nav link

## Activity Logging

All suggestion actions are logged to the activities table:
- User submits suggestion
- Admin approves/rejects suggestion

Logs appear in Dashboard → Recent Activity
