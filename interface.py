import streamlit as st
import data_collection
import subprocess
import re
import logging
import time
from datetime import datetime, timedelta

# Set logging level to WARNING (ignores DEBUG and INFO logs)
logging.basicConfig(level=logging.WARNING)

# Path to your logo image
logo_path = "assets/logo1.png"

# Function to clean output
def clean_output(output):
    if output is None:
        return ""
    # Removes escape sequences and unnecessary control characters
    return re.sub(r'\x1b\[?.*?[\@-~]', '', output)

# Function to generate response using the Ollama model
def generate_ollama_response(prompt):
    try:
        result = subprocess.run(
            ['ollama', 'run', 'llama2', prompt],
            capture_output=True,
            text=True
        )

        # Clean unwanted escape sequences from stderr and stdout
        stdout_clean = clean_output(result.stdout)

        # Log the raw outputs for debugging
        st.write(f"Your questions has been generated, click on proceed to move further")

        # Only return the cleaned output if it's valid
        if stdout_clean:
            return stdout_clean.strip()
        else:
            st.warning("Ollama returned no output.")
            return None

    except Exception as e:
        st.error(f"Error interacting with Ollama: {e}")
        return None

# Layout: Logo and App Title
col1, col2 = st.columns([1, 8])
with col1:
    st.image(logo_path, width=80)  # Adjust logo size
with col2:
    st.markdown(
        "<h1 style='margin: 0; color: white;'>Interactive Interview App</h1>",
        unsafe_allow_html=True
    )

# App Workflow Stages
if "stage" not in st.session_state:
    st.session_state["stage"] = "greeting"

if st.session_state["stage"] == "greeting":
    st.subheader("Welcome to the Interview Preparation App!")
    st.write("Let's start by getting to know you better.")

    # Collect Basic Information
    full_name = st.text_input("Full Name", placeholder="Enter your full name")
    email = st.text_input("Email Address", placeholder="Enter your email")
    phone = st.text_input("Phone Number", placeholder="Enter your phone number")
    years_of_experience = st.number_input("Years of Experience", min_value=0, step=1)
    desired_position = st.text_input("Desired Position(s)", placeholder="Enter your desired position")
    current_location = st.text_input("Current Location", placeholder="Enter your current location")

    # Tech Stack Selection
    tech_stack = st.multiselect(
        "Select your Tech Stack",
        options=["Python", "Java", "C#", "JavaScript", "React", "Django", "Flask", "TensorFlow", "PyTorch", "SQL", "NoSQL"],
        help="Select all the technologies you are familiar with."
    )

    # Proceed Button
    if st.button("Proceed"):
        if all([full_name, email, phone, years_of_experience >= 0, desired_position, current_location, tech_stack]):
            # Save User Data to Session State and CSV
            user_data = {
                "Name": full_name,
                "Email": email,
                "Phone": phone,
                "Experience": years_of_experience,
                "Position": desired_position,
                "Location": current_location,
                "Tech Stack": ", ".join(tech_stack),
            }
            data_collection.save_to_csv(user_data)

            st.session_state["basic_info"] = user_data

            # Generate Questions
            tech_stack_str = ", ".join(tech_stack)
            prompt = f"Generate only three question for each of the following technologies: {tech_stack_str} for a person with experience of {years_of_experience} years."

            with st.spinner(text="Generating questions... Please wait..."):
                generated_text = generate_ollama_response(prompt)

            if generated_text:
                # Process and Display Questions
                questions = re.findall(r'^\s*(.*?)\?', generated_text, re.MULTILINE)
                if questions:
                    st.session_state["questions"] = questions
                    st.session_state["answers"] = [""] * len(questions)  # Initialize empty answers
                    st.session_state["reading_start_time"] = datetime.now()  # Record the start time
                    st.session_state["stage"] = "reading_time"
                else:
                    st.warning("No valid questions generated. Please try again.")
            else:
                st.warning("Failed to generate questions. Check your input or try later.")
        else:
            st.warning("Please fill out all fields before proceeding.")
elif st.session_state["stage"] == "reading_time":
    st.subheader("Review the Questions")

    # Calculate review time based on the number of questions
    total_questions = len(st.session_state["questions"])
    review_duration = timedelta(minutes=1 * total_questions)  # 1 minutes per question

    st.write(f"Take your time to review the questions. You have {1 * total_questions} minutes to read them before proceeding to the answering section.")
    
    # Display Questions
    for idx, question in enumerate(st.session_state["questions"]):
        st.write(f"**Q{idx + 1}: {question}?**")

    # Initialize the start time if it's not already set
    if "reading_start_time" not in st.session_state:
        st.session_state["reading_start_time"] = datetime.now()

    # Timer logic
    timer_placeholder = st.empty()  # Create a placeholder for the timer

    if st.button("Next Step"):
        st.session_state["stage"] = "questions"
        st.rerun()

    while True:
        time_elapsed = datetime.now() - st.session_state["reading_start_time"]
        time_remaining = max(0, (review_duration - time_elapsed).total_seconds())

        # Display the countdown timer
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        timer_placeholder.markdown(
            f"<h3 style='color: red;'>Time remaining: {minutes:02}:{seconds:02}</h3>",
            unsafe_allow_html=True
        )

        if time_remaining <= 0:
            # Move to the next stage after time expires
            st.session_state["stage"] = "questions"
            st.rerun()
            break  # Exit the loop

        time.sleep(1)  # Update every second

    # Proceed to the next stage manually with a button (if user wants to move before time expires)
    

elif st.session_state["stage"] == "questions":
    st.subheader("Answer the Following Questions")

    total_questions = len(st.session_state["questions"])
    answer_duration = timedelta(minutes=5 * total_questions)

    if "question_start_time" not in st.session_state:
        st.session_state["question_start_time"] = datetime.now()


    timer_placeholder = st.empty()

    if st.button("Submit Answers"):
        # Display User Answers
        st.success("Thank you for submitting your answers!")
        for idx, (question, answer) in enumerate(zip(st.session_state["questions"], st.session_state["answers"])):
            st.write(f"**Q{idx + 1}: {question}?**")
            st.write(f"Your Answer: {answer}")

        st.session_state["stage"] = "completed"

    for idx, question in enumerate(st.session_state["questions"]):
        st.write(f"**Q{idx + 1}: {question}?**")
        st.session_state["answers"][idx] = st.text_area(f"Your Answer to Q{idx + 1}", key=f"answer_{idx}")

    while True:
        time_elapsed = datetime.now() - st.session_state["question_start_time"]
        time_remaining = max(0, (answer_duration - time_elapsed).total_seconds())

        # Display the countdown timer
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        timer_placeholder.markdown(
            f"<h3 style='color: red;'>Time remaining: {minutes:02}:{seconds:02}</h3>",
            unsafe_allow_html=True
        )

        if time_remaining <= 0:
            # Move to the next stage after time expires
            st.session_state["stage"] = "completed"
            st.rerun()
            break  # Exit the loop

        time.sleep(1)

    

elif st.session_state["stage"] == "completed":
    st.subheader("Interview Preparation Completed!")
    st.write("Thank you for using the Interactive Interview App.")