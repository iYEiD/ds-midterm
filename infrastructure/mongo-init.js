// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

db = db.getSiblingDB('nba_scraper');

// Create collections
db.createCollection('raw_scraped_data');
db.createCollection('processed_stats');
db.createCollection('scraping_metadata');
db.createCollection('query_history');

// Create indexes for raw_scraped_data
db.raw_scraped_data.createIndex({ url: 1 }, { unique: true });
db.raw_scraped_data.createIndex({ timestamp: -1 });
db.raw_scraped_data.createIndex({ status: 1 });

// Create indexes for processed_stats
db.processed_stats.createIndex({ player_name: 1 });
db.processed_stats.createIndex({ "metadata.season_type": 1 });
db.processed_stats.createIndex({ "metadata.scraped_at": -1 });
db.processed_stats.createIndex({ player_name: 1, "metadata.season_type": 1 }, { unique: true });

// Create indexes for scraping_metadata
db.scraping_metadata.createIndex({ url: 1 });
db.scraping_metadata.createIndex({ last_scraped: -1 });

// Create indexes for query_history
db.query_history.createIndex({ timestamp: -1 });
db.query_history.createIndex({ query_text: "text" });

print('MongoDB initialization completed successfully!');
print('Collections created:');
db.getCollectionNames().forEach(function(collection) {
    print('  - ' + collection);
});
