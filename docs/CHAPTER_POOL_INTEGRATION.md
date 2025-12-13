# Chapter-to-Pool Integration

## Overview
Chapters and question pools are now fully integrated. When teachers lock/unlock chapters for specific game modes, the question pools automatically update to reflect which questions are available.

## How It Works

### Automatic Synchronization
Every time a chapter is modified (added, edited, deleted, or locked/unlocked), the system automatically synchronizes the question pools:

1. **Test Yourself Pool** - Contains questions from all chapters where `locked_test_yourself = false`
2. **Level-Based Pool** - Contains questions from all chapters where `locked_level_mode = false`
3. **Endless Mode Pool** - Not affected by chapter locks (always uses all questions)

### Sync Function
The `sync_question_pools_with_chapters()` function:
- Runs automatically after any chapter modification
- Collects question IDs from unlocked chapters for each mode
- Updates `question_pools.json` accordingly
- Logs sync results to console

## Teacher Workflow

### Managing Chapter Access
1. Navigate to **Teacher Dashboard** → **Manage Chapters**
2. Use the lock toggle buttons to control chapter availability:
   - 🔓 **Test Yourself Lock** - Controls access in Test Yourself mode
   - 🔓 **Level Mode Lock** - Controls access in Level mode

### Example Scenarios

#### Scenario 1: Progressive Chapter Release
```
Chapter 1: Unlocked for both modes ✅
Chapter 2: Locked for both modes 🔒
Chapter 3: Locked for both modes 🔒

Result:
- Test Yourself: Only Chapter 1 questions available
- Level Mode: Only Chapter 1 levels visible
```

#### Scenario 2: Different Mode Access
```
Chapter 1: Unlocked for Test Yourself, Locked for Level Mode
Chapter 2: Locked for Test Yourself, Unlocked for Level Mode

Result:
- Test Yourself: Only Chapter 1 questions
- Level Mode: Only Chapter 2 levels
```

#### Scenario 3: Mixed Access
```
Chapter 1: Unlocked for both ✅
Chapter 2: Unlocked for Test Yourself only
Chapter 3: Unlocked for Level Mode only

Result:
- Test Yourself: Chapters 1 & 2 questions
- Level Mode: Chapters 1 & 3 levels
```

## Student Experience

### Test Yourself Mode
- Students see only unlocked chapters on the chapter selection screen
- Locked chapters display 🔒 indicator and "Locked" button
- Questions in the test come only from selected unlocked chapter

### Level Mode
- Chapter sections show lock status
- Locked chapters have overlay: "🔒 Locked by Teacher"
- Only levels from unlocked chapters are playable

## Technical Details

### Modified Routes
All chapter modification routes now call `sync_question_pools_with_chapters()`:
- `/teacher/add-chapter` - Syncs after creating chapter
- `/teacher/edit-chapter` - Syncs after updating chapter
- `/teacher/delete-chapter` - Syncs after removing chapter
- `/teacher/toggle-chapter-lock` - Syncs after lock status change

### Data Flow
```
Teacher Action (Lock/Unlock)
    ↓
Update chapters.json
    ↓
sync_question_pools_with_chapters()
    ↓
Load all chapters
    ↓
Filter by lock status for each mode
    ↓
Update question_pools.json
    ↓
Students see updated questions
```

### Console Logging
When sync runs, you'll see output like:
```
[SYNC] Updated pools - Test Yourself: 100, Level Mode: 50 questions
```

## Benefits

### For Teachers
- ✅ **Single Source of Truth** - Manage access in one place (chapters)
- ✅ **No Manual Pool Updates** - Question pools update automatically
- ✅ **Flexible Control** - Different access per game mode
- ✅ **Progressive Unlocking** - Release content gradually

### For Students
- ✅ **Clear Visibility** - Know which chapters are available
- ✅ **Consistent Experience** - Chapter locks apply uniformly
- ✅ **No Confusion** - Can't access locked content

## Testing

### Verify Integration
1. Go to Teacher Dashboard → Manage Chapters
2. Toggle a chapter lock for Test Yourself
3. Check `data/question_pools.json` - the `test_yourself` pool should update
4. Go to student view and verify chapter appears locked/unlocked
5. Repeat for Level Mode lock

### Expected Behavior
- Locking chapter removes its questions from that mode's pool
- Unlocking chapter adds questions back to pool
- Changes are immediate and persistent
- No manual intervention needed

## Migration Notes

### Existing Question Pools
If you have manually configured question pools:
- First sync will overwrite pool question IDs based on chapter locks
- Backup `question_pools.json` before first use if needed
- Pool settings (difficulty, time limits, etc.) are preserved

### New Installations
- Default chapter comes unlocked for both modes
- All 100 questions available initially
- Teachers can start locking chapters immediately

## Future Enhancements

Possible improvements:
- Partial chapter unlocking (select specific levels)
- Time-based auto-unlocking
- Student progress-based unlocking
- Per-student chapter access control

## Troubleshooting

### Pool Not Updating
- Check console for `[SYNC]` logs
- Verify `chapters.json` has correct lock flags
- Ensure chapter has `question_ids` array
- Restart server if needed

### Missing Questions
- Verify chapter is unlocked for the specific mode
- Check that chapter's `question_ids` contains the questions
- Use AI Arrange feature to distribute questions properly

### Lock Toggle Not Working
- Check browser console for errors
- Verify you're logged in as teacher
- Confirm AJAX request completes successfully
- Check `chapters.json` for updated timestamps

## Related Documentation
- [Chapter System Guide](DOCUMENTATION.md#chapters)
- [AI Question Arrangement](DOCUMENTATION.md#ai-arrangement)
- [Question Pools Reference](JSON_REFERENCE.md#question-pools)
