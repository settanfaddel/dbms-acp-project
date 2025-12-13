from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecret123"   # change this

def get_db():
    return sqlite3.connect("database.db")


def init_db():
    # Create activities table if not exists
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fullname TEXT NOT NULL,
            email TEXT NOT NULL,
            sdg_category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    con.commit()
    con.close()


def log_activity(user_id, message):
    try:
        con = get_db()
        cur = con.cursor()
        cur.execute("INSERT INTO activities (user_id, message) VALUES (?, ?)", (user_id, message))
        con.commit()
        con.close()
    except Exception:
        # Swallow logging errors so they don't crash the app
        pass

def get_initials(fullname):
    parts = fullname.split()
    initials = "".join([p[0] for p in parts])
    return initials.upper()[:2]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            con = get_db()
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT id, fullname, role, password FROM users WHERE email = ?", (email,))
            user = cur.fetchone()
            con.close()

            if user and password == user[3]:  # You will replace with hashed password later
                session["user_id"] = user[0]
                session["fullname"] = user[1]
                session["role"] = user[2]
                session["avatar"] = get_initials(user[1])
                session["email"] = email

                return redirect("/")

            return render_template("login.html", error="Invalid email or password")
        except sqlite3.OperationalError as e:
            return render_template("login.html", error="Database error. Please try again later.")
        except Exception as e:
            return render_template("login.html", error="An error occurred. Please try again.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")

        try:
            # Determine role: only allow specifying role if current session user is admin
            requested_role = request.form.get("role", "user")
            role = requested_role if session.get("role") == "admin" else "user"

            con = get_db()
            cur = con.cursor()
            
            # Check if email already exists
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cur.fetchone():
                con.close()
                return render_template("register.html", error="Email already registered")
            
            # Insert new user
            cur.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                       (fullname, email, password, role))
            con.commit()
            # get the new user's id for logging
            new_user_id = cur.lastrowid
            con.close()

            # Log activity: if created by admin, include actor, otherwise register event
            if session.get('role') == 'admin' and session.get('user_id'):
                log_activity(session.get('user_id'), f"Admin {session.get('fullname')} created user {fullname} (role={role})")
            else:
                log_activity(new_user_id, f"New user registered: {fullname}")

            return redirect("/login?registered=true")
        except Exception as e:
            return render_template("register.html", error=f"Registration failed: {str(e)}")

    return render_template("register.html")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/login")

    try:
        con = get_db()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT message, created_at FROM activities ORDER BY created_at DESC LIMIT 10")
        activities = cur.fetchall()
        con.close()
    except Exception:
        activities = []

    return render_template("dashboard.html", activities=activities)

@app.route("/manage")
def manage():
    if not session.get("user_id") or session.get("role") != "admin":
        return redirect("/login")
    
    try:
        con = get_db()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT id, fullname, email, role FROM users ORDER BY role DESC, fullname")
        users = cur.fetchall()
        
        # Count stats
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admins_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        regular_users_count = cur.fetchone()[0]
        
        con.close()
        # Read optional messages from query params
        success_message = request.args.get('success')
        error_message = request.args.get('error')

        return render_template("manage.html", users=users, admins_count=admins_count, regular_users_count=regular_users_count,
                       success_message=success_message, error_message=error_message)
    except Exception as e:
        return render_template("manage.html", users=[], admins_count=0, regular_users_count=0, error_message="Error loading users")


@app.route("/update-user/<int:user_id>", methods=["POST"])
def update_user(user_id):
    if not session.get("user_id") or session.get("role") != "admin":
        return redirect("/login")

    # Prevent changing your own role to avoid accidentally locking out all admins
    if user_id == session.get("user_id"):
        return redirect("/manage?error=Cannot change your own role")

    try:
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "user")

        con = get_db()
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # fetch previous state for logging
        cur.execute("SELECT fullname, role FROM users WHERE id = ?", (user_id,))
        prev = cur.fetchone()
        prev_fullname = prev[0] if prev else ''
        prev_role = prev[1] if prev else ''

        # If password provided, update it; otherwise leave as-is
        if password:
            cur.execute("UPDATE users SET fullname = ?, email = ?, password = ?, role = ? WHERE id = ?",
                       (fullname, email, password, role, user_id))
        else:
            cur.execute("UPDATE users SET fullname = ?, email = ?, role = ? WHERE id = ?",
                       (fullname, email, role, user_id))

        con.commit()
        con.close()

        # Log specific changes
        actor_id = session.get('user_id')
        if prev_role and prev_role != role:
            log_activity(actor_id, f"Admin {session.get('fullname')} changed role of {prev_fullname} from {prev_role} to {role}")
        else:
            log_activity(actor_id, f"Admin {session.get('fullname')} updated user {fullname} (id={user_id})")

        return redirect("/statistics")
    except sqlite3.IntegrityError:
        return redirect("/manage?error=Email already exists")
    except Exception as e:
        return redirect("/manage?error=Error updating user")

@app.route("/add-user", methods=["POST"])
def add_user():
    if not session.get("user_id") or session.get("role") != "admin":
        return redirect("/login")
    
    try:
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "user")
        
        con = get_db()
        cur = con.cursor()
        cur.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
               (fullname, email, password, role))
        new_user_id = cur.lastrowid
        con.commit()
        con.close()

        # Log activity
        log_activity(session.get('user_id'), f"Admin {session.get('fullname')} added user {fullname} (role={role})")

        return redirect("/manage?success=User added successfully")
    except sqlite3.IntegrityError:
        return redirect("/manage?error=Email already exists")
    except Exception as e:
        return redirect("/manage?error=Error adding user")

@app.route("/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if not session.get("user_id") or session.get("role") != "admin":
        return redirect("/login")
    
    # Prevent deleting yourself
    if user_id == session.get("user_id"):
        return redirect("/manage?error=Cannot delete your own account")
    
    try:
        con = get_db()
        cur = con.cursor()
        # fetch fullname for logging
        cur.execute("SELECT fullname FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        fullname = row[0] if row else ''

        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        con.commit()
        con.close()

        # Log activity
        log_activity(session.get('user_id'), f"Admin {session.get('fullname')} deleted user {fullname} (id={user_id})")

        return redirect("/manage?success=User deleted successfully")
    except Exception as e:
        return redirect("/manage?error=Error deleting user")

@app.route("/statistics")
def statistics():
    if not session.get("user_id"):
        return redirect("/login")
    
    try:
        con = get_db()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # Get user counts
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'moderator'")
        moderator_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        regular_user_count = cur.fetchone()[0]
        
        con.close()
        
        # Calculate percentages
        admin_percentage = round((admin_count / total_users * 100)) if total_users > 0 else 0
        moderator_percentage = round((moderator_count / total_users * 100)) if total_users > 0 else 0
        regular_percentage = round((regular_user_count / total_users * 100)) if total_users > 0 else 0
        
        # Calculate active sessions (simulated)
        active_sessions = max(1, int(total_users * 0.3))
        active_percentage = round((active_sessions / total_users * 100)) if total_users > 0 else 0
        
        # Growth simulation
        user_growth = 12
        
        # Weekly user registration data (simulated growth trend)
        week1_users = max(1, total_users // 6)
        week2_users = max(1, int(week1_users * 1.2))
        week3_users = max(1, int(week2_users * 1.3))
        week4_users = max(1, int(week3_users * 1.15))
        week5_users = max(1, int(week4_users * 1.25))
        week6_users = max(1, int(week5_users * 1.1))
        
        # Database size (simulated)
        db_size = 245
        
        # Last updated
        from datetime import datetime
        last_updated = datetime.now().strftime("%H:%M")
        
        return render_template(
            "statistics.html",
            total_users=total_users,
            admin_count=admin_count,
            moderator_count=moderator_count,
            regular_user_count=regular_user_count,
            admin_percentage=admin_percentage,
            moderator_percentage=moderator_percentage,
            regular_percentage=regular_percentage,
            active_sessions=active_sessions,
            active_percentage=active_percentage,
            user_growth=user_growth,
            week1_users=week1_users,
            week2_users=week2_users,
            week3_users=week3_users,
            week4_users=week4_users,
            week5_users=week5_users,
            week6_users=week6_users,
            db_size=db_size,
            last_updated=last_updated
        )
    except Exception as e:
        return render_template("statistics.html", error=f"Error loading statistics: {str(e)}")


@app.route("/suggestions")
def suggestions():
    if not session.get("user_id"):
        return redirect("/login")

    try:
        con = get_db()
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Fetch all suggestions, optionally filter by status
        status_filter = request.args.get('status', 'all')
        if status_filter != 'all':
            cur.execute('''
                SELECT id, fullname, email, sdg_category, title, description, status, created_at 
                FROM suggestions WHERE status = ? ORDER BY created_at DESC
            ''', (status_filter,))
        else:
            cur.execute('''
                SELECT id, fullname, email, sdg_category, title, description, status, created_at 
                FROM suggestions ORDER BY created_at DESC
            ''')
        suggestions_list = cur.fetchall()

        # Get counts by status
        cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'pending'")
        pending_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'approved'")
        approved_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'rejected'")
        rejected_count = cur.fetchone()[0]

        con.close()

        success_message = request.args.get('success')
        error_message = request.args.get('error')

        return render_template(
            "suggestions.html",
            suggestions=suggestions_list,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            current_status=status_filter,
            success_message=success_message,
            error_message=error_message
        )
    except Exception as e:
        return render_template("suggestions.html", error_message=f"Error loading suggestions: {str(e)}", suggestions=[], pending_count=0, approved_count=0, rejected_count=0, current_status='all', success_message=None)


@app.route("/submit-suggestion", methods=["POST"])
def submit_suggestion():
    if not session.get("user_id"):
        return redirect("/login")

    try:
        user_id = session.get("user_id")
        fullname = session.get("fullname")
        email = request.form.get("email")
        sdg_category = request.form.get("sdg_category")
        title = request.form.get("title")
        description = request.form.get("description")

        if not all([email, sdg_category, title, description]):
            return redirect("/suggestions?error=All fields are required")

        con = get_db()
        cur = con.cursor()
        cur.execute('''
            INSERT INTO suggestions (user_id, fullname, email, sdg_category, title, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, fullname, email, sdg_category, title, description))
        con.commit()
        con.close()

        # Log activity
        log_activity(user_id, f"{fullname} submitted a suggestion about {sdg_category}: {title}")

        return redirect("/suggestions?success=Suggestion submitted successfully!")
    except Exception as e:
        return redirect("/suggestions?error=Error submitting suggestion")


@app.route("/update-suggestion/<int:suggestion_id>", methods=["POST"])
def update_suggestion(suggestion_id):
    if not session.get("user_id") or session.get("role") != "admin":
        return redirect("/login")

    try:
        new_status = request.form.get("status", "pending")
        
        # Validate status
        if new_status not in ["pending", "approved", "rejected"]:
            return redirect("/suggestions?error=Invalid status")

        con = get_db()
        cur = con.cursor()
        
        # Get current suggestion status before update
        cur.execute("SELECT status FROM suggestions WHERE id = ?", (suggestion_id,))
        result = cur.fetchone()
        if not result:
            con.close()
            return redirect("/suggestions?error=Suggestion not found")
        
        current_status = result[0]
        
        # Update the suggestion
        cur.execute("UPDATE suggestions SET status = ? WHERE id = ?", (new_status, suggestion_id))
        con.commit()
        con.close()

        # Log activity with action type
        action = "approved" if new_status == "approved" else "rejected" if new_status == "rejected" else "marked as pending"
        log_activity(session.get("user_id"), f"Admin {session.get('fullname')} {action} suggestion #{suggestion_id}")

        # Provide feedback on what action was taken
        success_msg = f"Suggestion {action.split()[-1]}!"
        return redirect(f"/suggestions?success={success_msg}")
    except Exception as e:
        return redirect("/suggestions?error=Error updating suggestion")

if __name__ == "__main__":
    # Ensure DB schema for activities exists on startup
    try:
        init_db()
    except Exception:
        pass

    app.run(debug=True, host="0.0.0.0", port=5000)
