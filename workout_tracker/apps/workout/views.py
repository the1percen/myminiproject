from django.shortcuts import render, redirect
from django.contrib import messages # access django's `messages` module.
from .models import User, Workout, Exercise
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from dotenv import load_dotenv
import os
from decouple import config
from google import genai

load_dotenv()
logger = logging.getLogger(__name__)
client = genai.Client(api_key=config("GEMINI_API_KEY"))


def login(request):
    """If GET, load login page, if POST, login user."""

    if request.method == "GET":
        return render(request, "workout/index.html")

    if request.method == "POST":
        # Validate login data:
        validated = User.objects.login(**request.POST)
        try:
            # If errors, reload login page with errors:
            if len(validated["errors"]) > 0:
                logger.info("User could not be logged in.")
                # Loop through errors and Generate Django Message for each with custom level and tag:
                for error in validated["errors"]:
                    messages.error(request, error, extra_tags='login')
                # Reload login page:
                return redirect("/")
        except KeyError:
            # If validation successful, set session, and load dashboard based on user level:
            logger.info("User passed validation and is logged in.")

            # Set session to validated User:
            request.session["user_id"] = validated["logged_in_user"].id

            # Fetch dashboard data and load appropriate dashboard page:
            return redirect("/dashboard")

def register(request):
    """If GET, load registration page; if POST, register user."""

    if request.method == "GET":
        return render(request, "workout/register.html")

    if request.method == "POST":
        # Validate registration data:
        validated = User.objects.register(**request.POST)
        # If errors, reload register page with errors:
        try:
            if len(validated["errors"]) > 0:
                logger.info("User could not be registered.")
                # Loop through errors and Generate Django Message for each with custom level and tag:
                for error in validated["errors"]:
                    messages.error(request, error, extra_tags='registration')
                # Reload register page:
                return redirect("/user/register/")
        except KeyError:
            # If validation successful, set session and load dashboard based on user level:
            logger.info("User passed validation and has been created.")
            # Set session to validated User:
            request.session["user_id"] = validated["logged_in_user"].id
            # Load Dashboard:
            return redirect('/dashboard')

def logout(request):
    """Logs out current user."""

    try:
        # Deletes session:
        del request.session['user_id']
        # Adds success message:
        messages.success(request, "You have been logged out.", extra_tags='logout')

    except KeyError:
        pass

    # Return to index page:
    return redirect("/")

def dashboard(request):
    """Loads dashboard."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        # Get recent workouts for logged in user:
        recent_workouts = Workout.objects.filter(user__id=user.id).order_by('-id')[:4]

        # Get workout stats
        total_workouts = Workout.objects.filter(user__id=user.id).count()
        completed_workouts = Workout.objects.filter(user__id=user.id, completed=True).count()
        total_exercises = Exercise.objects.filter(workout__user__id=user.id).count()

        # Gather any page data:
        data = {
            'user': user,
            'recent_workouts': recent_workouts,
            'total_workouts': total_workouts,
            'completed_workouts': completed_workouts,
            'total_exercises': total_exercises,
        }

        # Load dashboard with data:
        return render(request, "workout/dashboard.html", data)

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def new_workout(request):
    """If GET, load new workout; if POST, submit new workout."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        # Gather any page data:
        data = {
            'user': user,
        }

        if request.method == "GET":
            # If get request, load `add workout` page with data:
            return render(request, "workout/add_workout.html", data)

        if request.method == "POST":
            # Unpack request.POST for validation as we must add a field and cannot modify the request.POST object itself as it's a tuple:
            workout = {
                "name": request.POST["name"],
                "description": request.POST["description"],
                "user": user
            }

            # Begin validation of a new workout:
            validated = Workout.objects.new(**workout)

            # If errors, reload register page with errors:
            try:
                if len(validated["errors"]) > 0:
                    logger.info("Workout could not be created.")
                    # Loop through errors and Generate Django Message for each with custom level and tag:
                    for error in validated["errors"]:
                        messages.error(request, error, extra_tags='workout')
                    # Reload workout page:
                    return redirect("/workout")
            except KeyError:
                # If validation successful, load newly created workout page:
                logger.info("Workout passed validation and has been created.")

                id = str(validated['workout'].id)
                # Load workout:
                return redirect('/workout/' + id)

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def workout(request, id):
    """View workout."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        # Gather any page data:
        data = {
            'user': user,
            'workout': Workout.objects.get(id=id),
            'exercises': Exercise.objects.filter(workout__id=id).order_by('-updated_at'),
        }

        # If get request, load workout page with data:
        return render(request, "workout/workout.html", data)

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def all_workouts(request):
    """Loads `View All` Workouts page."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        workout_list = Workout.objects.filter(user__id=user.id).order_by('-id')

        page = request.GET.get('page', 1)

        paginator = Paginator(workout_list, 12)
        try:
            workouts = paginator.page(page)
        except PageNotAnInteger:
            workouts = paginator.page(1)
        except EmptyPage:
            workouts = paginator.page(paginator.num_pages)

        # Gather any page data:
        data = {
            'user': user,
            'workouts': workouts,
        }

        # Load dashboard with data:
        return render(request, "workout/all_workouts.html", data)

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def exercise(request, id):
    """If POST, submit new exercise, if GET delete exercise."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        if request.method == "GET":

            # Delete exercise by exercise id (from hidden field):
            Exercise.objects.get(id=request.GET["exercise_id"]).delete()

            return redirect("/workout/" + id)

        if request.method == "POST":

            # Unpack request.POST for validation as we must add a field and cannot modify the request.POST object itself as it's a tuple:
            exercise = {
                "name": request.POST["name"],
                "weight": request.POST["weight"],
                "repetitions": request.POST["repetitions"],
                "workout": Workout.objects.get(id=id),
            }

            logger.info(exercise)
            # Begin validation of a new exercise:
            validated = Exercise.objects.new(**exercise)

            # If errors, reload register page with errors:
            try:
                if len(validated["errors"]) > 0:
                    logger.info("Exercise could not be created.")

                    # Loop through errors and Generate Django Message for each with custom level and tag:
                    for error in validated["errors"]:
                        messages.error(request, error, extra_tags='exercise')

                    # Reload workout page:
                    return redirect("/workout/" + id)
            except KeyError:
                # If validation successful, load newly created workout page:
                logger.info("Exercise passed validation and has been created.")

                # Reload workout:
                return redirect('/workout/' + id)

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def edit_workout(request, id):
    """If GET, load edit workout; if POST, update workout."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        # Gather any page data:
        data = {
            'user': user,
            'workout': Workout.objects.get(id=id),
            'exercises': Exercise.objects.filter(workout__id=id),
        }

        if request.method == "GET":
            # If get request, load edit workout page with data:
            return render(request, "workout/edit_workout.html", data)

        if request.method == "POST":
            # If post request, validate update workout data:
            # Unpack request object and build our custom tuple:
            workout = {
                'name': request.POST['name'],
                'description': request.POST['description'],
                'workout_id': data['workout'].id,
            }

            # Begin validation of updated workout:
            validated = Workout.objects.update(**workout)

            # If errors, reload register page with errors:
            try:
                if len(validated["errors"]) > 0:
                    logger.info("Workout could not be edited.")
                    # Loop through errors and Generate Django Message for each with custom level and tag:
                    for error in validated["errors"]:
                        messages.error(request, error, extra_tags='edit')
                    # Reload workout page:
                    return redirect("/workout/" + str(data['workout'].id) + "/edit")
            except KeyError:
                # If validation successful, load newly created workout page:
                logger.info("Edited workout passed validation and has been updated.")

                # Load workout:
                return redirect("/workout/" + str(data['workout'].id))

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def delete_workout(request, id):
    """Delete a workout (POST only)."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        if request.method == "POST":
            # Delete workout:
            Workout.objects.get(id=id).delete()
            messages.success(request, "Workout deleted successfully.")
            return redirect('/dashboard/')

        # If GET, redirect back to workout
        return redirect(f'/workout/{id}/')

    except (KeyError, User.DoesNotExist) as err:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def complete_workout(request, id):
    """If POST, complete a workout."""

    try:
        # Check for valid session:
        user = User.objects.get(id=request.session["user_id"])

        if request.method == "GET":
            # If get request, bring back to workout page.
            # Note, for now, GET request for this method not being utilized:
            return redirect("/workout/" + id)

        if request.method == "POST":

            # Update Workout.completed field for this instance:
            workout = Workout.objects.get(id=id)
            workout.completed = True
            workout.save()

            logger.info("Workout completed.")

            # Return to workout:
            return redirect('/workout/' + id)

    except (KeyError, User.DoesNotExist) as err:
        # If existing session not found:
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

def tos(request):
    """GET terms of service / user agreement."""

    return render(request, "workout/legal/tos.html")

def profile(request):
    """View and update user profile."""
    try:
        user = User.objects.get(id=request.session["user_id"])

        if request.method == "POST":
            # Update username
            new_username = request.POST.get("username", "").strip()
            new_email = request.POST.get("email", "").strip()

            errors = []
            if len(new_username) < 2:
                errors.append("Username must be at least 2 characters.")
            if len(new_email) < 5:
                errors.append("Email must be at least 5 characters.")

            # Check if username taken by another user
            existing = User.objects.filter(username=new_username).exclude(id=user.id)
            if existing.exists():
                errors.append("Username is already taken.")

            if errors:
                for error in errors:
                    messages.error(request, error, extra_tags='profile')
                return redirect("/profile/")

            user.username = new_username
            user.email = new_email

            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']

            user.save()
            messages.success(request, "Profile updated successfully!", extra_tags='profile')
            return redirect("/profile/")

        # GET request
        data = {
            'user': user,
            'total_workouts': Workout.objects.filter(user__id=user.id).count(),
            'completed_workouts': Workout.objects.filter(user__id=user.id, completed=True).count(),
            'total_exercises': Exercise.objects.filter(workout__user__id=user.id).count(),
        }
        return render(request, "workout/profile.html", data)

    except (KeyError, User.DoesNotExist):
        messages.info(request, "You must be logged in to view this page.", extra_tags="invalid_session")
        return redirect("/")

@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            # Generate AI response with fitness-focused system prompt
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=(
                    f"You are an expert fitness and workout assistant chatbot named FitBot. "
                    f"You help users with workout plans, exercise form tips, nutrition advice, "
                    f"recovery strategies, and motivation. Be friendly, encouraging, and professional. "
                    f"Use emojis sparingly to keep it engaging. Keep responses concise but helpful. "
                    f"If asked about medical conditions, recommend consulting a doctor. "
                    f"\n\nUser message: {user_message}"
                ),
            )

            bot_reply = response.text.strip()
            return JsonResponse({"reply": bot_reply})

        except Exception as e:
            return JsonResponse({"reply": f"Error: {str(e)}"})

    return render(request, "workout/chatbot.html")

@csrf_exempt
def ai_advice(request, id):
    """Generate AI advice for a workout."""
    try:
        user = User.objects.get(id=request.session["user_id"])
        workout_obj = Workout.objects.get(id=id)

        if request.method == "POST":
            exercises = Exercise.objects.filter(workout__id=id)
            exercise_list = ", ".join([f"{e.name} ({e.weight}lbs x {e.repetitions} reps)" for e in exercises])

            prompt = (
                f"You are an expert fitness trainer. Analyze this workout and provide advice:\n"
                f"Workout: {workout_obj.name}\n"
                f"Description: {workout_obj.description}\n"
                f"Exercises: {exercise_list if exercise_list else 'No exercises added yet'}\n\n"
                f"Provide:\n"
                f"1. Overall assessment of the workout\n"
                f"2. Tips for improvement\n"
                f"3. Safety considerations\n"
                f"4. Suggested complementary exercises\n"
                f"Keep it concise and actionable."
            )

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            advice = response.text.strip()

            # Save to workout
            workout_obj.ai_advice = advice
            workout_obj.save()

            return JsonResponse({"advice": advice})

        return JsonResponse({"error": "POST required"}, status=405)

    except (KeyError, User.DoesNotExist):
        return JsonResponse({"error": "Authentication required"}, status=401)
    except Workout.DoesNotExist:
        return JsonResponse({"error": "Workout not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def ai_plan(request, id):
    """Generate AI workout plan."""
    try:
        user = User.objects.get(id=request.session["user_id"])
        workout_obj = Workout.objects.get(id=id)

        if request.method == "POST":
            prompt = (
                f"You are a certified personal trainer. Create a detailed 3-day workout plan based on:\n"
                f"Workout focus: {workout_obj.name}\n"
                f"Description: {workout_obj.description}\n\n"
                f"Format each day with:\n"
                f"- Day title and focus area\n"
                f"- 5-6 exercises with sets, reps, and rest periods\n"
                f"- Warm-up and cool-down suggestions\n"
                f"Keep it practical and progressive."
            )

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            plan = response.text.strip()

            workout_obj.ai_plan = plan
            workout_obj.save()

            return JsonResponse({"plan": plan})

        return JsonResponse({"error": "POST required"}, status=405)

    except (KeyError, User.DoesNotExist):
        return JsonResponse({"error": "Authentication required"}, status=401)
    except Workout.DoesNotExist:
        return JsonResponse({"error": "Workout not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)