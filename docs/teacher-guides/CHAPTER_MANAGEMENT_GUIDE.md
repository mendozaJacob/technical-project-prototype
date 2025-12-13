# 📚 Chapter Management System Guide

## Overview

The Chapter Management System allows teachers to organize questions into logical chapters and control which content is available in each game mode independently.

## Key Features

### 📖 Chapter Organization
- **Create Chapters**: Define chapter name, description, and display order
- **Assign Questions**: Select specific questions to include in each chapter
- **Level Ranges**: Map chapters to game levels (e.g., Chapter 1 → Levels 1-10)
- **Visual Cards**: Each chapter displayed as a card with statistics

### 🔒 Per-Mode Lock System

Each chapter has **independent lock controls** for three game modes:

1. **Test Yourself Mode Lock** 🔒
   - Controls question availability in Test Yourself mode
   - Locked chapters exclude their questions from test pool
   
2. **Level Mode Lock** 🔒
   - Controls question availability in Adventure/Level mode
   - Locked chapters exclude their questions from level gameplay
   
3. **Endless Mode Lock** 🔒
   - Controls question availability in Endless survival mode
   - Locked chapters exclude their questions from endless pool

### ⚡ Auto-Sync Feature

Question pools automatically synchronize when:
- Chapter lock status changes
- Questions are assigned/unassigned to chapters
- New chapters are created or deleted

**Auto-Sync Behavior:**
- ✅ **Auto-Enable**: Pools activate when questions become available
- ❌ **Auto-Disable**: Pools deactivate when all chapters are locked (0 questions)
- 📊 **Logging**: Sync results logged for debugging

## How to Use

### Creating a Chapter

1. Navigate to **Teacher Dashboard** → **Chapter Management**
2. Click **"+ Add New Chapter"** button
3. Fill in the form:
   - **Chapter Name**: e.g., "Chapter 1: Introduction"
   - **Description**: Brief description of chapter content
   - **Order**: Display order (1, 2, 3...)
   - **Level Range**: Number of levels (creates levels 1-N)
   - **Lock Status**: Check boxes for modes you want to lock
   - **Questions**: Select questions to include
4. Click **"Add Chapter"**

### Editing a Chapter

1. In the Chapter Management page, find the chapter
2. Click the **"Edit"** button on the chapter card
3. Modify any fields (name, description, locks, questions)
4. Click **"Update Chapter"**

### Lock/Unlock Toggles

In the chapter table, you can quickly toggle locks:
- Click **🔒 Locked** to unlock
- Click **🔓 Unlocked** to lock
- Changes apply immediately

### Viewing Chapter Statistics

Each chapter card displays:
- 📝 Total questions assigned
- 🔒 Lock status for each mode (Locked/Unlocked)
- 📊 Level range covered

## Question Pool Integration

### How Pools Work

The system maintains three question pools:

1. **`test_yourself`** - Questions for Test Yourself mode
2. **`level_based`** - Questions for Adventure/Level mode  
3. **`endless_mode`** - Questions for Endless survival mode

### Sync Logic

When chapters are locked/unlocked:

```python
# For each chapter:
if not chapter.locked_test_yourself:
    # Add chapter's questions to test_yourself pool
    
if not chapter.locked_level_mode:
    # Add chapter's questions to level_based pool
    
if not chapter.locked_endless_mode:
    # Add chapter's questions to endless_mode pool
```

### Pool States

**Active Pool** (enabled=true):
- Has questions available (at least 1 unlocked chapter)
- Game mode is playable
- Questions randomly selected from pool

**Disabled Pool** (enabled=false):
- No questions available (all chapters locked)
- Game mode shows "No questions available" message
- Auto-disables when question count reaches 0

## Use Cases

### Scenario 1: Progressive Chapter Release

**Goal**: Release chapters sequentially as students progress

**Setup**:
1. Create Chapter 1 with levels 1-10, unlocked for all modes
2. Create Chapter 2 with levels 11-20, **locked for all modes**
3. Create Chapter 3 with levels 21-30, **locked for all modes**

**As students progress**:
- Week 2: Unlock Chapter 2 for Level Mode only
- Week 3: Unlock Chapter 2 for Test Yourself
- Week 4: Unlock Chapter 3...

### Scenario 2: Mode-Specific Content

**Goal**: Different content for different game modes

**Setup**:
1. **Basic Questions Chapter**:
   - Unlocked for Level Mode ✓
   - Unlocked for Test Yourself ✓
   - Locked for Endless Mode ✗
   
2. **Advanced Questions Chapter**:
   - Locked for Level Mode ✗
   - Unlocked for Test Yourself ✓
   - Unlocked for Endless Mode ✓

**Result**: 
- Level Mode: Only basic questions
- Test Yourself: All questions
- Endless Mode: Only advanced questions

### Scenario 3: Test Preparation

**Goal**: Prepare students for an upcoming test

**Setup**:
1. **Lock Level Mode** for all chapters (disable regular gameplay)
2. **Unlock Test Yourself** for relevant chapters
3. Students focus on test preparation

**After Test**:
1. Unlock Level Mode again
2. Lock Test Yourself to encourage gameplay

## Technical Details

### Data Structure

**chapters.json**:
```json
{
  "chapters": [
    {
      "id": 1,
      "name": "Chapter 1: Getting Started",
      "description": "Introduction to basic concepts",
      "order": 1,
      "question_ids": [1, 2, 3, 4, 5],
      "locked_test_yourself": false,
      "locked_level_mode": false,
      "locked_endless_mode": false,
      "level_range": [1, 2, 3, 4, 5],
      "created_at": "2025-11-26T00:00:00",
      "updated_at": "2025-11-26T01:04:18"
    }
  ],
  "metadata": {
    "last_updated": "2025-11-26T01:04:18",
    "version": "1.0.0",
    "total_chapters": 1
  }
}
```

**question_pools.json**:
```json
{
  "pools": {
    "test_yourself": {
      "name": "Test Yourself Mode",
      "description": "Questions for test yourself practice mode",
      "question_ids": [1, 2, 3, 4, 5],
      "enabled": true,
      "question_count": 5
    },
    "level_based": {
      "name": "Level-Based Mode",
      "description": "Questions for adventure/level mode",
      "question_ids": [1, 2, 3, 4, 5],
      "enabled": true,
      "question_count": 5
    },
    "endless_mode": {
      "name": "Endless Mode",
      "description": "Questions for endless survival mode",
      "question_ids": [1, 2, 3, 4, 5],
      "enabled": true,
      "question_count": 5
    }
  }
}
```

### API Endpoints

- `GET /teacher/chapters` - View chapter management page
- `POST /teacher/add-chapter` - Create new chapter
- `POST /teacher/edit-chapter/<id>` - Update chapter
- `POST /teacher/delete-chapter/<id>` - Delete chapter
- `POST /teacher/toggle-chapter-lock/<id>/<mode>` - Toggle lock status
- `POST /teacher/sync-pools` - Manually trigger pool sync

### Sync Function

Located in `app.py` (lines 4887-4925):

```python
def sync_question_pools_with_chapters():
    """Sync question pools with chapter lock states"""
    # Load chapters and pools
    # For each chapter, check lock status
    # Add questions from unlocked chapters to pools
    # Update pool enabled status based on question count
    # Save updated pools
    # Return sync results
```

## Best Practices

### 1. Plan Chapter Structure
- Group related content together
- Keep chapters focused on specific topics
- Assign appropriate level ranges

### 2. Use Locks Strategically
- Don't lock all chapters at once
- Keep at least one chapter unlocked per mode
- Use locks to control pacing

### 3. Regular Sync Checks
- Monitor pool sync logs
- Verify pools enable/disable correctly
- Check question counts after changes

### 4. Test After Changes
- Play each game mode after chapter updates
- Verify correct questions appear
- Ensure locked content is hidden

## Troubleshooting

### Issue: Pool shows 0 questions but chapters are unlocked

**Solution**: 
1. Check if questions are actually assigned to chapters
2. Run manual sync: POST to `/teacher/sync-pools`
3. Check sync logs for errors

### Issue: Game mode not available

**Solution**:
1. Check if pool is enabled in `question_pools.json`
2. Verify at least one chapter is unlocked for that mode
3. Confirm chapters have questions assigned

### Issue: Wrong questions appearing in game mode

**Solution**:
1. Verify chapter lock status matches intention
2. Check question assignments to chapters
3. Clear browser cache and restart game

## Future Enhancements

Potential improvements for future versions:

- **Chapter Prerequisites**: Require completing Chapter 1 before unlocking Chapter 2
- **Bulk Operations**: Lock/unlock multiple chapters at once
- **Chapter Analytics**: Track performance by chapter
- **Question Difficulty Tags**: Filter by difficulty within chapters
- **Chapter Import/Export**: Share chapter configurations
- **Student-Specific Locks**: Customize content per student

---

**Last Updated**: November 27, 2025  
**Version**: 1.0.0  
**Author**: Technical Project Team
