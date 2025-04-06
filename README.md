Inspiration:
In today's day and age it feels like even reading more than 10 pages of a research paper takes hours. It takes hours to digest concepts and properly retain it. Digesting complex concepts and actually remembering them is even harder. We built ResearchRot to make research more accessible and digestible for students. Our goal? Help students spend less time reading and more time innovating.
We realized that there are three main types of learning that students utilize auditory, visual, and deliberate practice. ResearchRot serves students with auditory learning through the podcast, the brain rot video for visual learners, and flashcards/mnemonic devices for deliberate practice.
What it does
ResearchRot turns overwhelming research papers into bite-sized, Gen Z-friendly learning tools. With just a few clicks, students can:
	•	Generate concise summaries
	•	Listen to a podcast version of the paper
	•	Create flashcards to test their understanding
	•	Use fun, themed mnemonic devices to retain key ideas
	•	Watch brain rot- subway surfers while learning important concepts
How we built it with our brains!
Utilized react for our front end development and python backend via fastAPI. For generating summaries, flashcards, and mnemonic aids, we tapped into the power of Google Gemini, using creative prompts to keep things fun and memorable. We used ElevenLabs to convert summaries into podcasts and even created a “brain rot” style video—yes, we added Subway Surfers gameplay in the background.
Challenges we ran into
We were really hoping to generate a song with lyrics that would help students have a earworm based on their research paper however, the resources available for this were limited and many did not allow for generation via api key.
Accomplishments that we're proud of
We built something that we—and our friends—would actually use. That’s a win in our book.
What we learned
We learned that using generative AI can truly help our projects go much farther. We began with this idea and soon realized that Google Gemini was very helpful for generating tools for students.
What's next for ResearchRot
We hope to add a option for students to develop songs based on the research papers. This is not something we were able to generate in this project.

To run it, add an env file with GEMINI_API_KEY, ELEVENLABS_API_KEY
