#!/bin/bash

# Setup script for debug overlay
echo "🔧 Setting up debug overlay for The Commons frontend..."

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create .env.local file in frontend directory
ENV_FILE="frontend/.env.local"

echo "📝 Creating $ENV_FILE..."

# Check if file already exists
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  $ENV_FILE already exists. Updating debug environment variables..."
    
    # Update VITE_DEBUG_OVERLAY
    if grep -q "VITE_DEBUG_OVERLAY" "$ENV_FILE"; then
        sed -i '' 's/VITE_DEBUG_OVERLAY=.*/VITE_DEBUG_OVERLAY=true/' "$ENV_FILE"
    else
        echo "VITE_DEBUG_OVERLAY=true" >> "$ENV_FILE"
    fi
    
    # Update VITE_DEBUG_RAW
    if grep -q "VITE_DEBUG_RAW" "$ENV_FILE"; then
        sed -i '' 's/VITE_DEBUG_RAW=.*/VITE_DEBUG_RAW=true/' "$ENV_FILE"
    else
        echo "VITE_DEBUG_RAW=true" >> "$ENV_FILE"
    fi
    
    # Update VITE_USE_HARDCODED_DATA
    if grep -q "VITE_USE_HARDCODED_DATA" "$ENV_FILE"; then
        sed -i '' 's/VITE_USE_HARDCODED_DATA=.*/VITE_USE_HARDCODED_DATA=false/' "$ENV_FILE"
    else
        echo "VITE_USE_HARDCODED_DATA=false" >> "$ENV_FILE"
    fi
else
    # Create new file
    cat > "$ENV_FILE" << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG_OVERLAY=true
VITE_DEBUG_RAW=true
VITE_USE_HARDCODED_DATA=false
EOF
fi

echo "✅ Debug overlay enabled!"
echo ""
echo "🎯 Next steps:"
echo "1. Restart your frontend development server"
echo "2. Look for a small 'D' button in the top-right corner"
echo "3. Click it to toggle the debug overlay"
echo ""
echo "🔧 To disable the debug overlay later, set VITE_DEBUG_OVERLAY=false in $ENV_FILE"
