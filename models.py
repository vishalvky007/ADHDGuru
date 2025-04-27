from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, CHATS_COLLECTION, MESSAGES_COLLECTION, JOURNAL_COLLECTION
import time
import uuid
from datetime import datetime
from operator import itemgetter

# Initialize in-memory fallback storage
class InMemoryDB:
    def __init__(self):
        self.collections = {
            CHATS_COLLECTION: {},
            MESSAGES_COLLECTION: {},
            JOURNAL_COLLECTION: {}
        }
    
    def insert_one(self, collection_name, data):
        # Generate a unique ID if not present
        if '_id' not in data:
            data['_id'] = str(uuid.uuid4())
        
        # Store in the appropriate collection
        self.collections[collection_name][data['_id']] = data
        return type('obj', (object,), {'inserted_id': data['_id']})
    
    def find(self, collection_name, query=None):
        # Simple implementation for find
        if not query:
            results = list(self.collections[collection_name].values())
        else:
            # Basic filtering implementation
            results = []
            for item in self.collections[collection_name].values():
                match = True
                for key, value in query.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                if match:
                    results.append(item)
        
        # Return a MockCursor that can handle sort and limit operations
        return MockCursor(results)
    
    def update_one(self, collection_name, query, update_data):
        # Simple implementation for update_one
        modified_count = 0
        for doc_id, doc in self.collections[collection_name].items():
            match = True
            for key, value in query.items():
                if key == '_id':
                    if str(doc_id) != str(value):
                        match = False
                        break
                elif key not in doc or doc[key] != value:
                    match = False
                    break
            
            if match:
                # Apply updates
                if '$set' in update_data:
                    for k, v in update_data['$set'].items():
                        doc[k] = v
                modified_count += 1
                break
        
        return type('obj', (object,), {'modified_count': modified_count})
    
    def delete_one(self, collection_name, query):
        # Simple implementation for delete_one
        deleted_count = 0
        doc_id_to_delete = None
        
        for doc_id, doc in self.collections[collection_name].items():
            match = True
            for key, value in query.items():
                if key == '_id':
                    if str(doc_id) != str(value):
                        match = False
                        break
                elif key not in doc or doc[key] != value:
                    match = False
                    break
            
            if match:
                doc_id_to_delete = doc_id
                break
        
        if doc_id_to_delete:
            del self.collections[collection_name][doc_id_to_delete]
            deleted_count = 1
        
        return type('obj', (object,), {'deleted_count': deleted_count})

# Mock cursor for in-memory storage
class MockCursor:
    def __init__(self, results):
        self.results = results
        self.sort_field = None
        self.sort_direction = 1  # 1 for ascending, -1 for descending
        self.limit_value = None
    
    def sort(self, field_or_list, direction=None):
        # Handle both direct field name and list of tuples formats
        if isinstance(field_or_list, str):
            self.sort_field = field_or_list
            if direction is not None:
                self.sort_direction = direction
        elif isinstance(field_or_list, list) and len(field_or_list) > 0:
            # If it's a list of tuples, use the first one
            self.sort_field = field_or_list[0][0]
            self.sort_direction = field_or_list[0][1]
        
        return self
    
    def limit(self, limit_value):
        self.limit_value = limit_value
        return self
    
    def __iter__(self):
        # Apply sorting if specified
        results = self.results.copy()
        
        if self.sort_field:
            # Sort results by the specified field
            def get_sort_key(item):
                if self.sort_field in item:
                    return item[self.sort_field]
                return None
            
            results.sort(key=get_sort_key, reverse=(self.sort_direction == -1))
        
        # Apply limit if specified
        if self.limit_value is not None:
            results = results[:self.limit_value]
        
        return iter(results)
    
    def __len__(self):
        return len(self.results)
    
    def __getitem__(self, idx):
        return self.results[idx]

# Connect to MongoDB or use in-memory fallback
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.server_info()
    
    # Get database
    db = client[DB_NAME]
    
    # Get collections
    chats_collection = db[CHATS_COLLECTION]
    messages_collection = db[MESSAGES_COLLECTION]
    journal_collection = db[JOURNAL_COLLECTION]
    
    # Connection status message
    print(f"Connected to MongoDB with URI: {MONGO_URI}")
    
    # Flag to track connection status
    using_fallback = False
    
except Exception as e:
    # MongoDB connection failed, use in-memory fallback
    print(f"Warning: MongoDB connection failed ({e}). Using in-memory storage fallback.")
    
    # Create in-memory collections
    in_memory_db = InMemoryDB()
    
    # Create collection proxies as classes
    class CollectionProxy:
        def __init__(self, name):
            self.collection_name = name
            
        def insert_one(self, data):
            return in_memory_db.insert_one(self.collection_name, data)
            
        def find(self, query=None):
            if query is None:
                query = {}
            return in_memory_db.find(self.collection_name, query)
            
        def update_one(self, query, update):
            return in_memory_db.update_one(self.collection_name, query, update)
            
        def delete_one(self, query):
            return in_memory_db.delete_one(self.collection_name, query)
    
    # Create collection instances
    chats_collection = CollectionProxy(CHATS_COLLECTION)
    messages_collection = CollectionProxy(MESSAGES_COLLECTION)
    journal_collection = CollectionProxy(JOURNAL_COLLECTION)
    
    # Flag to track connection status
    using_fallback = True 