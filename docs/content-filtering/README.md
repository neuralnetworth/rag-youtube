# Content Filtering Documentation

This directory contains comprehensive documentation for the RAG-YouTube content filtering system.

## Documentation Structure

### 📘 For Users

1. **[User Guide](user-guide.md)**
   - How to use each filter type
   - Best practices and tips
   - Troubleshooting common issues
   - Example use cases

### 🔧 For Developers

2. **[Technical Overview](overview.md)**
   - System architecture
   - Core components
   - Data flow
   - Performance considerations

3. **[Implementation Guide](implementation-guide.md)**
   - Step-by-step implementation details
   - Code examples
   - Testing strategies
   - Troubleshooting

4. **[Technical Reference](technical-reference.md)**
   - API endpoints
   - Data structures
   - Class references
   - Configuration options

### 🎯 Playlist Filtering Extension

5. **[Playlist Filtering](../playlist-filtering/)**
   - Implementation summary
   - Testing checklist
   - Additional features built on top of base filtering

## Quick Links

- **Start Here**: [User Guide](user-guide.md) for using filters
- **Architecture**: [Technical Overview](overview.md) for system design
- **Implementation**: [Implementation Guide](implementation-guide.md) for code details
- **API Reference**: [Technical Reference](technical-reference.md) for developers

## Feature Summary

The content filtering system provides:

- ✅ **Caption Filtering**: Search only videos with transcripts
- ✅ **Category Filtering**: Filter by content type (educational, daily updates, etc.)
- ✅ **Quality Filtering**: Filter by content density and technical depth
- ✅ **Date Range Filtering**: Limit results to specific time periods
- ✅ **Playlist Filtering**: Filter by YouTube playlist membership
- ✅ **Combined Filtering**: Use multiple filters together

## System Status

- **Core Filtering**: ✅ Complete and tested
- **UI Integration**: ✅ Fully implemented
- **API Endpoints**: ✅ Documented and functional
- **Performance**: ✅ Sub-50ms filter application
- **Test Coverage**: ✅ Comprehensive test suite

## Getting Started

### For Users
1. Read the [User Guide](user-guide.md)
2. Open http://localhost:8000
3. Try different filter combinations

### For Developers
1. Review the [Technical Overview](overview.md)
2. Check the [Implementation Guide](implementation-guide.md)
3. Reference the [API Documentation](technical-reference.md)

## Related Documentation

- [Main README](../../README.md) - Project overview
- [CLAUDE.md](../../CLAUDE.md) - Development instructions
- [FastAPI Docs](http://localhost:8000/docs) - Live API documentation