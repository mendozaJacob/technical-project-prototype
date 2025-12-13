# AI Question Assignment to Chapters and Levels

## Overview
When generating questions with AI, you can now automatically assign them to specific chapters and levels, streamlining the question organization workflow.

## How to Use

### Step 1: Generate Questions
1. Navigate to **Teacher Dashboard** → **AI Question Generator**
2. Upload your curriculum content (PDF, DOCX, TXT, or MD file)
3. Fill in the generation parameters:
   - Topic/Subject
   - Difficulty Level
   - Number of Questions
   - Question Types
   - Additional Context (optional)

### Step 2: Select Assignment Options

#### Assign to Chapter (Optional)
- **Dropdown:** "Assign to Chapter (Optional)"
- Select a chapter from your existing chapters
- Generated questions will be automatically added to the selected chapter
- Leave as "-- Don't assign to chapter --" to skip chapter assignment

#### Assign to Level (Optional)
- **Dropdown:** "Assign to Level (Optional)"
- Select a level (1-10)
- Generated questions will be automatically added to that level
- Leave as "-- Don't assign to level --" to skip level assignment

### Step 3: Generate and Save
1. Click **"🎯 Generate Questions with AI"**
2. Review the AI-generated questions
3. Select which questions to include (all are checked by default)
4. Click **"💾 Save Selected Questions"**
5. Questions are saved to the question bank AND assigned to the selected chapter/level

## What Happens Behind the Scenes

### Chapter Assignment
When you assign to a chapter:
- Questions are saved to `questions.json` with unique IDs
- Question IDs are added to the chapter's `question_ids` array
- Chapter's `updated_at` timestamp is updated
- Question pools are automatically synced (if chapter is unlocked)
- No duplicate IDs are created

### Level Assignment
When you assign to a level:
- Questions are saved to `questions.json` with unique IDs
- Question IDs are added to the level's `questions` array in `levels.json`
- No duplicate IDs are created
- Students will see these questions when playing that level

### Both Chapter and Level
You can assign to both simultaneously:
- Questions go to both the chapter and the level
- Ensures questions are available in multiple game modes
- Provides maximum flexibility for content organization

## Example Workflows

### Workflow 1: Progressive Chapter Building
```
1. Create "Chapter 1: Linux Basics"
2. Generate 10 beginner questions
3. Assign to: Chapter 1, Level 1
4. Generate 10 intermediate questions
5. Assign to: Chapter 1, Level 2
6. Continue building chapter progressively
```

### Workflow 2: Level-Specific Content
```
1. Upload "Advanced Networking.pdf"
2. Generate 20 advanced questions
3. Assign to: Level 8
4. Don't assign to chapter (general pool)
5. Questions available in Level 8 for all players
```

### Workflow 3: Chapter-Only Assignment
```
1. Upload "Database Administration.docx"
2. Generate 15 questions
3. Assign to: Chapter 3
4. Don't assign to level
5. Use AI Arrange later to distribute to levels
```

### Workflow 4: Question Bank Only
```
1. Generate questions from curriculum
2. Don't assign to chapter or level
3. Manually organize later via Chapter Management
4. Or use AI Arrange feature for automatic distribution
```

## Success Messages

After saving, you'll see detailed confirmation:

**Basic Save:**
```
Successfully added 10 questions to the question bank!
```

**With Chapter Assignment:**
```
Successfully added 10 questions to the question bank! Questions assigned to chapter: Chapter 1: Getting Started.
```

**With Level Assignment:**
```
Successfully added 10 questions to the question bank! Questions assigned to Level 5.
```

**With Both:**
```
Successfully added 10 questions to the question bank! Questions assigned to chapter: Chapter 2: Advanced Topics. Questions assigned to Level 7.
```

## Benefits

### Time Savings
- ✅ No manual assignment after generation
- ✅ Questions immediately available in gameplay
- ✅ One-step process from generation to deployment

### Organization
- ✅ Keep questions organized by chapter/level from the start
- ✅ Avoid loose questions in the general pool
- ✅ Clear content structure

### Flexibility
- ✅ Can skip assignment and organize manually later
- ✅ Can assign to both chapter and level simultaneously
- ✅ No restrictions on future reorganization

### Integration
- ✅ Works seamlessly with chapter system
- ✅ Automatically syncs question pools
- ✅ Respects chapter lock status
- ✅ Maintains data consistency

## Technical Details

### Question ID Management
- System automatically generates sequential IDs
- No conflicts with existing questions
- IDs are unique across all questions

### Data Files Updated
1. **questions.json** - New questions added with `ai_generated: true` flag
2. **chapters.json** - Chapter's `question_ids` updated (if chapter selected)
3. **levels.json** - Level's `questions` array updated (if level selected)
4. **question_pools.json** - Automatically synced via `sync_question_pools_with_chapters()`

### Duplicate Prevention
- System checks for existing IDs before adding
- Uses `set()` operations to avoid duplicates
- Safe to run multiple times

### Error Handling
- Invalid chapter ID → Skips chapter assignment, continues with save
- Invalid level → Skips level assignment, continues with save
- File errors → Logged to console, user sees generic error
- Questions always saved to question bank first

## Troubleshooting

### Questions Not Appearing in Chapter
- Check if chapter exists in Chapter Management
- Verify chapter ID matches dropdown selection
- Check console logs for assignment errors
- Refresh the Chapters page

### Questions Not Appearing in Level
- Verify level number (1-10)
- Check `levels.json` for the question IDs
- Ensure student has unlocked that level
- Check if chapter containing the level is unlocked

### Assignment Silently Fails
- Check browser console for JavaScript errors
- Check server terminal for DEBUG messages
- Verify file permissions on data directory
- Ensure JSON files are valid and writable

### Success Message Doesn't Show Assignment
- Assignment may have failed silently
- Check actual data files to confirm
- Verify chapter/level exists before generation
- Review server logs for error details

## Best Practices

### 1. Plan Your Structure First
- Create chapters before generating questions
- Decide on level distribution strategy
- Use AI Arrange feature for complex distributions

### 2. Generate in Batches
- Generate small batches (10-15 questions)
- Assign to specific targets immediately
- Easier to review and manage

### 3. Review Before Saving
- Uncheck poor quality questions
- Edit questions if needed (after saving)
- Verify question types match your needs

### 4. Use Descriptive Topics
- Helps AI generate better questions
- Makes organization clearer
- Easier to find questions later

### 5. Combine with Manual Organization
- Use assignment for initial placement
- Refine with Chapter Management tools
- Use AI Arrange for optimal distribution

## Related Features
- [Chapter Management System](CHAPTER_POOL_INTEGRATION.md)
- [AI Question Arrangement](DOCUMENTATION.md#ai-arrangement)
- [Question Pool Integration](CHAPTER_POOL_INTEGRATION.md#automatic-synchronization)

## Future Enhancements
Possible improvements:
- Assign to multiple chapters at once
- Assign to level ranges (e.g., Levels 5-7)
- Preview chapter/level before assignment
- Bulk reassignment tools
- Assignment history tracking
