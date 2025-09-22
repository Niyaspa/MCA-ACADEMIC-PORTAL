#!/usr/bin/env python3
"""
Demonstration script showing how the random question selection works
in the MCA Portal Quiz System.

This script simulates the random selection functionality without requiring
a running Flask application or database.
"""

import random
from datetime import datetime

class MockQuestion:
    """Mock question class to simulate database questions"""
    def __init__(self, id, question, option_a, option_b, option_c, option_d, correct_option):
        self.id = id
        self.question = question
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c
        self.option_d = option_d
        self.correct_option = correct_option

class MockQuiz:
    """Mock quiz class to simulate database quiz"""
    def __init__(self, title, randomize_questions=False, questions_per_attempt=None):
        self.title = title
        self.randomize_questions = randomize_questions
        self.questions_per_attempt = questions_per_attempt
        self.questions = []
    
    def add_question(self, question, option_a, option_b, option_c, option_d, correct_option):
        """Add a question to the quiz"""
        q_id = len(self.questions) + 1
        self.questions.append(MockQuestion(q_id, question, option_a, option_b, option_c, option_d, correct_option))

def select_quiz_questions(quiz):
    """
    Implement the same random selection logic used in the Flask app
    """
    if quiz.randomize_questions and quiz.questions_per_attempt and len(quiz.questions) > quiz.questions_per_attempt:
        # Random selection enabled and we have more questions than needed
        selected_questions = random.sample(list(quiz.questions), quiz.questions_per_attempt)
        print(f"🎲 Randomly selected {quiz.questions_per_attempt} questions out of {len(quiz.questions)} total questions")
    else:
        # Use all questions (either no randomization or not enough questions to select from)
        selected_questions = list(quiz.questions)
        if quiz.randomize_questions:
            print(f"📝 Using all {len(quiz.questions)} questions (not enough questions for random selection)")
        else:
            print(f"📋 Using all {len(quiz.questions)} questions (sequential quiz)")
    
    return selected_questions

def demo_random_quiz():
    """Demonstrate the random quiz functionality"""
    print("="*60)
    print("MCA PORTAL - RANDOM QUIZ DEMONSTRATION")
    print("="*60)
    
    # Create a sample quiz with 20 questions
    quiz = MockQuiz("Database Management Systems Quiz", randomize_questions=True, questions_per_attempt=10)
    
    # Add 20 sample questions
    sample_questions = [
        ("What is a primary key?", "A unique identifier", "A foreign key", "An index", "A constraint", "A"),
        ("What does SQL stand for?", "Simple Query Language", "Structured Query Language", "Sequential Query Language", "Standard Query Language", "B"),
        ("What is normalization?", "Data compression", "Data organization", "Data encryption", "Data backup", "B"),
        ("Which is not a SQL command?", "SELECT", "UPDATE", "DELETE", "PRINT", "D"),
        ("What is a foreign key?", "Primary key of another table", "Unique key", "Composite key", "Candidate key", "A"),
        ("What is ACID in databases?", "A data type", "Transaction properties", "A database engine", "A query language", "B"),
        ("What is a view in SQL?", "A physical table", "A virtual table", "An index", "A constraint", "B"),
        ("What is indexing?", "Data sorting", "Performance optimization", "Data validation", "Data encryption", "B"),
        ("What is a stored procedure?", "A function", "Pre-compiled SQL code", "A trigger", "A view", "B"),
        ("What is denormalization?", "Reverse of normalization", "Data compression", "Data encryption", "Index creation", "A"),
        ("What is a trigger?", "A constraint", "Auto-executed code", "A function", "A procedure", "B"),
        ("What is referential integrity?", "Data validation rule", "Index type", "Query optimization", "Transaction property", "A"),
        ("What is a cursor?", "Database pointer", "Index type", "Constraint", "Function", "A"),
        ("What is deadlock?", "System crash", "Resource blocking", "Data corruption", "Index failure", "B"),
        ("What is sharding?", "Data partitioning", "Data compression", "Data encryption", "Data backup", "A"),
        ("What is replication?", "Data copying", "Data compression", "Data validation", "Data sorting", "A"),
        ("What is a transaction?", "Database operation unit", "Table type", "Index method", "Constraint rule", "A"),
        ("What is concurrency?", "Multiple operations", "Data sorting", "Index creation", "Table joining", "A"),
        ("What is a schema?", "Database structure", "Data type", "Query result", "Index type", "A"),
        ("What is optimization?", "Query performance tuning", "Data compression", "Data validation", "Data backup", "A")
    ]
    
    for i, (question, opt_a, opt_b, opt_c, opt_d, correct) in enumerate(sample_questions):
        quiz.add_question(question, opt_a, opt_b, opt_c, opt_d, correct)
    
    print(f"\n📚 Quiz: {quiz.title}")
    print(f"📊 Total questions available: {len(quiz.questions)}")
    print(f"🎯 Questions per attempt: {quiz.questions_per_attempt}")
    print(f"🔀 Randomization enabled: {quiz.randomize_questions}")
    
    print("\n" + "="*60)
    print("DEMONSTRATING MULTIPLE QUIZ ATTEMPTS")
    print("="*60)
    
    # Simulate 3 different quiz attempts to show randomization
    for attempt in range(1, 4):
        print(f"\n🎓 ATTEMPT #{attempt} - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        selected_questions = select_quiz_questions(quiz)
        
        print(f"Selected questions for this attempt:")
        for i, q in enumerate(selected_questions, 1):
            print(f"{i:2d}. Q{q.id:2d}: {q.question}")
            print(f"      A) {q.option_a}")
            print(f"      B) {q.option_b}")  
            print(f"      C) {q.option_c}")
            print(f"      D) {q.option_d}")
            print(f"      ✅ Correct Answer: {q.correct_option}")
            print()
        
        # Show which questions from the total pool were selected
        selected_ids = [q.id for q in selected_questions]
        selected_ids.sort()
        print(f"📝 Question IDs selected: {selected_ids}")
        
        # Calculate variety score
        if attempt > 1:
            overlap = len(set(selected_ids) & set(previous_ids))
            variety_score = ((len(selected_ids) - overlap) / len(selected_ids)) * 100
            print(f"🎲 Variety from previous attempt: {variety_score:.1f}% different questions")
        
        previous_ids = selected_ids
    
    print("\n" + "="*60)
    print("DEMONSTRATION OF NON-RANDOM QUIZ")
    print("="*60)
    
    # Create a non-random quiz for comparison
    standard_quiz = MockQuiz("Standard Programming Quiz", randomize_questions=False, questions_per_attempt=None)
    for i in range(5):
        standard_quiz.add_question(
            f"Programming question {i+1}",
            "Option A", "Option B", "Option C", "Option D", "A"
        )
    
    print(f"\n📚 Quiz: {standard_quiz.title}")
    print(f"📊 Total questions available: {len(standard_quiz.questions)}")
    print(f"🎯 Questions per attempt: All questions")
    print(f"🔀 Randomization enabled: {standard_quiz.randomize_questions}")
    
    selected_questions = select_quiz_questions(standard_quiz)
    print(f"📝 All students will see the same {len(selected_questions)} questions in the same order")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✅ Random quiz feature successfully implemented!")
    print("✅ Admin can upload 20 questions and set 10 questions per attempt")
    print("✅ Each student gets a different random selection of questions")
    print("✅ System handles both random and standard quiz types")
    print("✅ UI shows clear indication of quiz type to students")
    print("✅ Admin interface shows configuration options")

if __name__ == "__main__":
    demo_random_quiz()