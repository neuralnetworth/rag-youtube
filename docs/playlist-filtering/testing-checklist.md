# Playlist Filtering Testing Checklist

## Testing Checklist for Content Filtering Features

### 1. **Basic UI Elements**
- [ ] Visit http://localhost:8000
- [ ] Check that the "Playlists" multi-select dropdown appears in the filter section
- [ ] Verify it shows playlist names with video counts (e.g., "SG Videos (40 videos)")
- [ ] Confirm playlists are sorted by video count (highest first)
- [ ] Check that the info text "(Hold Ctrl/Cmd to select multiple)" is visible

### 2. **Multi-Select Functionality**
- [ ] Click on a single playlist to select it
- [ ] Hold Ctrl (or Cmd on Mac) and click another playlist to select multiple
- [ ] Verify multiple playlists can be selected simultaneously
- [ ] Check that the "Clear Filters" button appears when playlists are selected

### 3. **Filter Application**
- [ ] Select one playlist (e.g., "OPEX Monthly: Live Market Analysis")
- [ ] Ask a question like "What is gamma?"
- [ ] Verify that returned sources are only from videos in that playlist
- [ ] Select multiple playlists and verify results come from any of the selected playlists

### 4. **Combined Filters**
- [ ] Select a playlist + check "Require captions"
- [ ] Verify results are filtered by both criteria
- [ ] Try playlist + category filter combination
- [ ] Test playlist + quality filter combination
- [ ] Test playlist + date range combination

### 5. **Clear Filters**
- [ ] Select multiple playlists
- [ ] Click "Clear Filters" button
- [ ] Verify all playlist selections are cleared
- [ ] Confirm the multi-select shows no selections

### 6. **Dark Mode**
- [ ] Toggle dark mode
- [ ] Verify the playlist multi-select has proper styling in dark mode
- [ ] Check that selected options are visible/readable
- [ ] Verify hover states work correctly

### 7. **API Endpoint**
- [ ] Visit http://localhost:8000/api/filters/options
- [ ] Verify the response includes a "playlists" object with playlist names and counts
- [ ] Check that playlist counts match UI display

### 8. **Edge Cases**
- [ ] Test with no playlists selected (should return all results)
- [ ] Select a playlist with very few videos and verify it limits results appropriately
- [ ] Test invalid filter combinations
- [ ] Test with empty search query but filters applied

### 9. **Performance**
- [ ] Verify filter application doesn't significantly slow down searches
- [ ] Check that the over-fetching strategy provides good results
- [ ] Test with maximum filters applied simultaneously

### 10. **Data Accuracy**
- [ ] Verify videos are correctly associated with their playlists
- [ ] Check that playlist counts are accurate
- [ ] Confirm filter statistics update when filters are applied

## Known Issues to Watch For

1. **Multi-select behavior**: Different browsers may handle Ctrl/Cmd differently
2. **Scroll position**: Multi-select dropdown should maintain scroll position
3. **Mobile compatibility**: Multi-select may need special handling on mobile devices

## Testing Environment

- **Browser**: Test in Chrome, Firefox, Safari (if available)
- **Dark mode**: Test in both light and dark modes
- **Screen sizes**: Test on desktop and mobile viewport sizes