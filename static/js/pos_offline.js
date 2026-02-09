const db = new Dexie("POSOfflineDB");

db.version(1).stores({
    salesQueue: "++id, created_at"
});
