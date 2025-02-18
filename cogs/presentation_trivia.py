import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import os
from dotenv import load_dotenv
import random
import asyncio
import io
from pptx import Presentation
import docx
import PyPDF2
import json
import traceback
import re

class PresentationTriviaView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=None)
        self.cog = cog
        self.original_interaction = interaction
        self.active = True
        self.waiting_for_answer = False
        self.current_question = 0  # Track current question index

    @discord.ui.button(label="Skip Question", style=discord.ButtonStyle.gray)
    async def skip_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle skipping to the next question"""
        if interaction.user == self.original_interaction.user:
            self.waiting_for_answer = False  # Stop waiting for current answer
            self.current_question += 1  # Move to next question
            await interaction.response.send_message("Skipping to next question...", ephemeral=True)
            # Signal the main loop to continue
            self.stop()
        else:
            await interaction.response.send_message("Only the person who started the trivia can skip questions!", ephemeral=True)

    @discord.ui.button(label="End Trivia", style=discord.ButtonStyle.red)
    async def end_trivia(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.original_interaction.user:
            self.active = False
            self.waiting_for_answer = False
            button.disabled = True
            await interaction.message.edit(view=self)
            await interaction.response.send_message("Trivia game ended! Thanks for playing! 📚")
            self.stop()
        else:
            await interaction.response.send_message("Only the person who started the trivia can end it!", ephemeral=True)

    async def wait_for_answer(self, bot, message, reactions):
        """Handle waiting for answer with cancellation support"""
        self.waiting_for_answer = True
        try:
            def check(reaction, user):
                return (user == self.original_interaction.user and 
                        str(reaction.emoji) in reactions and 
                        reaction.message.id == message.id)

            while self.waiting_for_answer and self.active:
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                    self.waiting_for_answer = False
                    return reaction, user
                except asyncio.TimeoutError:
                    self.waiting_for_answer = False
                    return None, None
                
        except Exception as e:
            print(f"Error in wait_for_answer: {e}")
            self.waiting_for_answer = False
            return None, None

class ContentUploadView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=300)
        self.cog = cog
        self.interaction = interaction

    @discord.ui.button(label="Paste Text", style=discord.ButtonStyle.primary, emoji="📝")
    async def paste_text(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons after selection
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        modal = ContentPasteModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Upload File", style=discord.ButtonStyle.green, emoji="📁")
    async def upload_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons after selection
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(
            "Please upload your file (txt, pdf, docx, pptx). You have 5 minutes."
        )
        
        def check(m):
            return (m.author == interaction.user and 
                   m.channel == interaction.channel and 
                   len(m.attachments) > 0)

        try:
            msg = await self.cog.bot.wait_for('message', timeout=300.0, check=check)
            
            if msg.attachments:
                file = msg.attachments[0]
                if not any(file.filename.endswith(ext) for ext in ['.txt', '.pdf', '.docx', '.pptx']):
                    await interaction.followup.send(
                        "Invalid file type. Please use .txt, .pdf, .docx, or .pptx files."
                    )
                    return
                
                processing_msg = await interaction.followup.send("Processing your file... ⏳")
                file_data = await file.read()
                content = await self.cog.process_file(file_data, file.filename)
                
                if not content or len(content.strip()) < 50:
                    await interaction.followup.send(
                        "Not enough valid content found in file. Please try a different file."
                    )
                    return
                
                await processing_msg.edit(content="File processed successfully! Generating quiz... 🎯")
                await self.cog.start_quiz(interaction, content)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("No file uploaded within 5 minutes. Please try again.")

class ContentPasteModal(discord.ui.Modal, title="Paste Your Content"):
    content = discord.ui.TextInput(
        label="Content",
        style=discord.TextStyle.paragraph,
        placeholder="Paste your content here...",
        required=True,
        max_length=4000
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        content = str(self.content)
        
        if len(content) < 50:
            await interaction.followup.send(
                "Content too short. Please provide more text."
            )
            return

        processing_msg = await interaction.followup.send(
            "Processing your content... ⏳"
        )
        
        # Start the quiz with the provided content
        await processing_msg.edit(content="Content processed! Generating quiz... 🎯")
        await self.cog.start_quiz(interaction, content)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.followup.send(
            f"An error occurred: {str(error)}",
            ephemeral=True
        )

class ContentChoiceView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=300)
        self.cog = cog
        self.interaction = interaction

    @discord.ui.button(label="Use Previous Content", style=discord.ButtonStyle.green, emoji="🔄")
    async def use_previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        content = self.cog.user_content.get(interaction.user.id)
        if content:
            # Disable buttons after selection
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            
            processing_msg = await interaction.followup.send("Generating quiz from previous content... 🎯")
            await self.cog.start_quiz(interaction, content)
        else:
            await interaction.followup.send("No previous content found. Please provide new content.")

    @discord.ui.button(label="New Content", style=discord.ButtonStyle.primary, emoji="📝")
    async def new_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons after selection
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(
            "Please paste your content or upload a file (txt, pdf, docx, pptx). You have 5 minutes."
        )

        def check(m):
            return (m.author == interaction.user and 
                   m.channel == interaction.channel and 
                   (m.content or m.attachments))

        try:
            msg = await self.cog.bot.wait_for('message', timeout=300.0, check=check)
            
            processing_msg = await interaction.followup.send("Processing your content... ⏳")
            
            if msg.attachments:
                file = msg.attachments[0]
                if not any(file.filename.endswith(ext) for ext in ['.txt', '.pdf', '.docx', '.pptx']):
                    await interaction.followup.send(
                        "Invalid file type. Please use .txt, .pdf, .docx, or .pptx files."
                    )
                    return
                    
                file_data = await file.read()
                content = await self.cog.process_file(file_data, file.filename)
            else:
                content = msg.content

            if not content or len(content.strip()) < 50:
                await interaction.followup.send(
                    "Not enough content provided. Please try again with more text."
                )
                return
            
            await processing_msg.edit(content="Content processed! Generating quiz... 🎯")
            await self.cog.start_quiz(interaction, content)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("No content received within 5 minutes. Please try again.")

class PresentationTrivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize Gemini
        load_dotenv()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        # Add content cache dictionary
        self.user_content = {}

    async def generate_questions(self, content: str) -> list:
        """Generate questions using Gemini AI"""
        try:
            if not content or len(content.strip()) < 50:
                print("Content too short or empty")
                return []

            print(f"Processing content length: {len(content)} characters")
            
            prompt = f"""You are a quiz generator. Generate up to 10 multiple-choice questions about the key concepts from this content.

REQUIRED FORMAT:
{{
    "questions": [
        {{
            "question": "What is the main concept described in...?",
            "correct_answer": "The correct answer",
            "incorrect_answers": [
                "First wrong answer",
                "Second wrong answer",
                "Third wrong answer"
            ],
            "explanation": "Explanation based on the content"
        }}
    ]
}}

CRITICAL RULES:
1. Generate as many questions as the content allows (up to 10)
2. Only create questions when there's enough content to support them
3. Focus on key concepts and important information
4. NO questions about:
   - Course metadata (instructors, chapters, etc.)
   - Formatting or presentation
5. Each question must have clear, distinct answers
6. All answers must come from the content
7. Quality over quantity - fewer good questions are better than many poor ones

Content to use:
{content[:4000]}"""
            
            print("Sending request to Gemini...")
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            
            def clean_json_text(text):
                text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
                text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()

            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if not json_match:
                    print("No JSON structure found")
                    return []
                
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                if 'questions' not in parsed:
                    print("Invalid JSON structure - missing questions array")
                    return []
                
                valid_questions = []
                seen_questions = set()
                metadata_keywords = ['instructor', 'professor', 'teacher', 'chapter', 
                                   'section', 'page', 'course', 'code', 'syllabus']
                
                for q in parsed['questions']:
                    try:
                        # Skip metadata questions
                        if any(keyword in q['question'].lower() for keyword in metadata_keywords):
                            continue
                            
                        if (isinstance(q, dict) and
                            all(key in q for key in ['question', 'correct_answer', 'incorrect_answers', 'explanation']) and
                            isinstance(q['incorrect_answers'], list) and 
                            len(q['incorrect_answers']) == 3):
                            
                            cleaned_q = {
                                'question': clean_json_text(q['question']),
                                'correct_answer': clean_json_text(q['correct_answer']),
                                'incorrect_answers': [clean_json_text(ans) for ans in q['incorrect_answers']],
                                'explanation': clean_json_text(q['explanation'])
                            }
                            
                            # Validate answer quality
                            answers = [cleaned_q['correct_answer']] + cleaned_q['incorrect_answers']
                            if (len(set(answers)) == 4 and  # All answers must be unique
                                all(len(ans.strip()) > 0 for ans in answers)):  # No empty answers
                                if cleaned_q['question'] not in seen_questions:
                                    seen_questions.add(cleaned_q['question'])
                                    valid_questions.append(cleaned_q)
                    except Exception as e:
                        print(f"Question validation error: {str(e)}")
                        continue
                
                num_questions = len(valid_questions)
                print(f"Successfully generated {num_questions} valid questions")
                
                if num_questions == 0:
                    print("No valid questions generated")
                    return []
                elif num_questions < 5:
                    print(f"Warning: Only generated {num_questions} questions")
                
                random.shuffle(valid_questions)
                return valid_questions  # Return all valid questions (up to 10)
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                return []
            
        except Exception as e:
            print(f"Question generation error: {str(e)}")
            return []

    def split_content(self, content: str) -> list:
        """Split content into manageable sections"""
        # Split on paragraphs or major punctuation
        sections = re.split(r'\n\n+|\. (?=[A-Z])', content)
        
        # Combine very short sections
        merged_sections = []
        current_section = ""
        
        for section in sections:
            if not section.strip():
                continue
            
            if len(current_section) + len(section) < 1000:
                current_section += " " + section
            else:
                if current_section:
                    merged_sections.append(current_section.strip())
                current_section = section
        
        if current_section:
            merged_sections.append(current_section.strip())
        
        return merged_sections

    def process_response(self, response_text: str) -> list:
        """Process and validate response from Gemini"""
        try:
            # Extract and clean JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                return []
            
            json_str = json_match.group()
            parsed = json.loads(json_str)
            
            if 'questions' not in parsed:
                return []
            
            # Clean and validate questions
            valid_questions = []
            for q in parsed['questions']:
                try:
                    if self.is_valid_question(q):
                        cleaned_q = self.clean_question(q)
                        valid_questions.append(cleaned_q)
                except:
                    continue
            
            return valid_questions
            
        except:
            return []

    def is_valid_question(self, question: dict) -> bool:
        """Validate question structure and content"""
        return (isinstance(question, dict) and
                all(key in question for key in ['question', 'correct_answer', 'incorrect_answers', 'explanation']) and
                isinstance(question['incorrect_answers'], list) and 
                len(question['incorrect_answers']) == 3)

    def clean_question(self, question: dict) -> dict:
        """Clean and format question text"""
        def clean_text(text):
            text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        return {
            'question': clean_text(question['question']),
            'correct_answer': clean_text(question['correct_answer']),
            'incorrect_answers': [clean_text(ans) for ans in question['incorrect_answers']],
            'explanation': clean_text(question['explanation'])
        }

    def validate_questions(self, questions: list) -> list:
        """Final validation of questions"""
        seen_questions = set()
        valid_questions = []
        
        for q in questions:
            if q['question'] not in seen_questions:
                seen_questions.add(q['question'])
                valid_questions.append(q)
        
        return valid_questions

    def clean_content(self, content: str) -> str:
        """Clean and prepare content for question generation"""
        if not content:
            return ""
            
        # Remove extra whitespace and normalize line endings
        content = content.strip()
        content = ' '.join(content.split())
        
        # Remove any empty lines
        content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())
        
        # Remove any special characters that might interfere with processing
        content = content.replace('\x00', '')
        
        return content

    async def process_file(self, file_data: bytes, filename: str) -> str:
        """Process different file types and extract text content"""
        try:
            text_content = ""
            
            if filename.endswith('.pptx'):
                prs = Presentation(io.BytesIO(file_data))
                for slide in prs.slides:
                    # Process all shapes in the slide
                    for shape in slide.shapes:
                        # Get text from text frames
                        if hasattr(shape, "text_frame"):
                            if shape.text_frame.text:
                                text_content += shape.text_frame.text.strip() + "\n"
                            # Get text from paragraphs in text frame
                            for paragraph in shape.text_frame.paragraphs:
                                for run in paragraph.runs:
                                    if run.text:
                                        text_content += run.text.strip() + "\n"
                        
                        # Get text from tables
                        if hasattr(shape, "table"):
                            for row in shape.table.rows:
                                for cell in row.cells:
                                    if cell.text:
                                        text_content += cell.text.strip() + "\n"
                        
                        # Get text from grouped shapes
                        if hasattr(shape, "shapes"):
                            for subshape in shape.shapes:
                                if hasattr(subshape, "text_frame"):
                                    if subshape.text_frame.text:
                                        text_content += subshape.text_frame.text.strip() + "\n"
                                if hasattr(subshape, "table"):
                                    for row in subshape.table.rows:
                                        for cell in row.cells:
                                            if cell.text:
                                                text_content += cell.text.strip() + "\n"
                    
            elif filename.endswith('.docx'):
                doc = docx.Document(io.BytesIO(file_data))
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_content += paragraph.text.strip() + "\n"
                    
            elif filename.endswith('.pdf'):
                pdf = PyPDF2.PdfReader(io.BytesIO(file_data))
                for page in pdf.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_content += text.strip() + "\n"
                    
            elif filename.endswith('.txt'):
                text_content = file_data.decode('utf-8')
            
            # Clean and validate content
            cleaned_content = self.clean_content(text_content)
            if len(cleaned_content) < 50:  # Minimum content length check
                print(f"Content too short after cleaning: {len(cleaned_content)} chars")
                return ""
                
            print(f"Successfully processed {filename}, extracted {len(cleaned_content)} chars")
            return cleaned_content
            
        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")
            return ""

    @app_commands.command(name="quiz", description="Start a quiz game from presentation content")
    @app_commands.describe(new_content="Start with new content? Default: Use previous content if available")
    async def presentation_trivia(self, interaction: discord.Interaction, new_content: bool = False):
        if not new_content and interaction.user.id in self.user_content:
            embed = discord.Embed(
                title="📚 Presentation Quiz",
                description="Would you like to use your previous content or provide new content?",
                color=discord.Color.blue()
            )
            view = ContentChoiceView(self, interaction)
            await interaction.response.send_message(embed=embed, view=view)
            return
            
        # If no previous content or user wants new content
        await interaction.response.send_message(
            "Please paste your content or upload a file (txt, pdf, docx, pptx). You have 5 minutes."
        )

        def check(m):
            return (m.author == interaction.user and 
                   m.channel == interaction.channel and 
                   (m.content or m.attachments))

        try:
            msg = await self.bot.wait_for('message', timeout=300.0, check=check)
            
            processing_msg = await interaction.followup.send("Processing your content... ⏳")
            
            if msg.attachments:
                file = msg.attachments[0]
                if not any(file.filename.endswith(ext) for ext in ['.txt', '.pdf', '.docx', '.pptx']):
                    await interaction.followup.send(
                        "Invalid file type. Please use .txt, .pdf, .docx, or .pptx files."
                    )
                    return
                    
                file_data = await file.read()
                content = await self.process_file(file_data, file.filename)
            else:
                content = msg.content

            if not content or len(content.strip()) < 50:
                await interaction.followup.send(
                    "Not enough content provided. Please try again with more text."
                )
                return
            
            await processing_msg.edit(content="Content processed! Generating quiz... 🎯")
            await self.start_quiz(interaction, content)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("No content received within 5 minutes. Please try again.")

    async def start_quiz(self, interaction: discord.Interaction, content: str):
        """Start the quiz with the provided content"""
        try:
            # Cache the content for this user
            self.user_content[interaction.user.id] = content
            
            # Generate questions
            questions = await self.generate_questions(content)
            if not questions:
                await interaction.followup.send("Unable to generate questions from the provided content. Please try with different content.")
                return

            # Start trivia game
            view = PresentationTriviaView(self, interaction)
            score = 0
            total_questions = len(questions)

            for i, question in enumerate(questions, 1):
                if not view.active:
                    break

                # Show progress
                progress = discord.Embed(
                    title="📚 Presentation Trivia",
                    description=f"Question {i} of {total_questions}\nCurrent Score: {score}/{i-1}",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=progress)

                # Format question
                question_embed = discord.Embed(
                    title="Question",
                    description=question['question'],
                    color=discord.Color.blue()
                )

                all_answers = question['incorrect_answers'] + [question['correct_answer']]
                random.shuffle(all_answers)

                for idx, answer in enumerate(all_answers, 1):
                    question_embed.add_field(
                        name=f"Option {idx}",
                        value=answer,
                        inline=False
                    )

                msg = await interaction.followup.send(embed=question_embed, view=view)

                # Add reactions
                reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
                for reaction in reactions:
                    await msg.add_reaction(reaction)

                # Wait for answer
                reaction, user = await view.wait_for_answer(self.bot, msg, reactions)
                
                if not view.active:  # If trivia was ended
                    break
                    
                if not reaction:  # If we timed out
                    timeout_embed = discord.Embed(
                        title="⏰ Time's Up!",
                        description=f"The correct answer was: **{question['correct_answer']}**",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=timeout_embed)
                    break

                selected_idx = reactions.index(str(reaction.emoji))
                selected_answer = all_answers[selected_idx]
                is_correct = selected_answer == question['correct_answer']

                if is_correct:
                    score += 1

                result_embed = discord.Embed(
                    title="Answer Result",
                    description=(
                        f"You selected: {selected_answer}\n\n"
                        f"{'✅ Correct!' if is_correct else '❌ Incorrect!'}\n"
                        f"The correct answer was: **{question['correct_answer']}**\n\n"
                        f"Explanation:\n{question.get('explanation', 'No explanation provided.')}"
                    ),
                    color=discord.Color.green() if is_correct else discord.Color.red()
                )
                await interaction.followup.send(embed=result_embed)

                if i < total_questions:
                    await asyncio.sleep(3)

            if view.active:  # Only show final score if trivia wasn't ended early
                final_embed = discord.Embed(
                    title="🎯 Trivia Complete!",
                    description=f"Final Score: {score}/{i}\nPercentage: {(score/i)*100:.1f}%",
                    color=discord.Color.gold()
                )
                await interaction.followup.send(embed=final_embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(PresentationTrivia(bot)) 