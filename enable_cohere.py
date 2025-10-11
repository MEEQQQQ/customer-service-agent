import boto3

# The Cohere model needs to be enabled in Bedrock Model Access
# This must be done through the AWS Console:
# 1. Go to: https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess
# 2. Click "Manage model access"
# 3. Enable "Cohere" models
# 4. Click "Save changes"

print("=" * 60)
print("ACTION REQUIRED: Enable Cohere Model Access")
print("=" * 60)
print("\n1. Open AWS Console:")
print("   https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess")
print("\n2. Click 'Manage model access'")
print("\n3. Check the box for 'Cohere' models")
print("\n4. Click 'Save changes'")
print("\n5. Wait 1-2 minutes for access to be granted")
print("\n6. Then run: python test_kb_after_access.py")
print("=" * 60)
