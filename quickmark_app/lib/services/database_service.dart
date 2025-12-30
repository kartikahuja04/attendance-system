import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/user_model.dart';
import '../models/attendance_record.dart';

class DatabaseService {
  static final DatabaseService _instance = DatabaseService._internal();
  static Database? _database;

  factory DatabaseService() {
    return _instance;
  }

  DatabaseService._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'quickmark.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    // Users table - stores student info and face embedding
    await db.execute('''
      CREATE TABLE users(
        student_id TEXT PRIMARY KEY,
        name TEXT,
        password TEXT,
        face_embedding TEXT,
        is_enrolled INTEGER DEFAULT 0,
        device_id TEXT,
        created_at TEXT
      )
    ''');

    // Attendance table - history
    await db.execute('''
      CREATE TABLE attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        session_id TEXT,
        subject TEXT,
        class_name TEXT,
        section TEXT,
        timestamp TEXT,
        status TEXT,
        FOREIGN KEY(student_id) REFERENCES users(student_id)
      )
    ''');

    // Timetable table - schedules
    await db.execute('''
      CREATE TABLE timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_of_week TEXT,
        subject TEXT,
        time_slot TEXT,
        room TEXT
      )
    ''');
    
    // Seed some dummy timetable data for demo
    await _seedTimetable(db);
  }
  
  Future<void> _seedTimetable(Database db) async {
    final days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    final subjects = ['Computer Networks', 'Database Management', 'Operating Systems', 'Software Engineering', 'AI & ML'];
    
    for (var day in days) {
      for (var i = 0; i < 3; i++) {
         await db.insert('timetable', {
           'day_of_week': day,
           'subject': subjects[i % subjects.length],
           'time_slot': '${9 + i}:00 AM - ${10 + i}:00 AM',
           'room': 'Lab ${i + 1}'
         });
      }
    }
  }

  // --- User Operations ---

  Future<bool> saveUser(User user) async {
    final db = await database;
    try {
      await db.insert(
        'users',
        user.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      return true;
    } catch (e) {
      print('Error saving user: $e');
      return false;
    }
  }

  Future<User?> getUser(String studentId) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'users',
      where: 'student_id = ?',
      whereArgs: [studentId],
    );

    if (maps.isNotEmpty) {
      return User.fromMap(maps.first);
    }
    return null;
  }
  
  Future<void> updateFaceEmbedding(String studentId, List<double> embedding) async {
     final db = await database;
     await db.update(
       'users',
       {'face_embedding': jsonEncode(embedding), 'is_enrolled': 1},
       where: 'student_id = ?',
       whereArgs: [studentId],
     );
  }

  // --- Attendance Operations ---

  Future<bool> markAttendance(AttendanceRecord record) async {
    final db = await database;
    try {
      await db.insert('attendance', record.toMap());
      return true;
    } catch (e) {
      print('Error marking attendance: $e');
      return false;
    }
  }

  Future<List<AttendanceRecord>> getAttendanceHistory(String studentId) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'attendance',
      where: 'student_id = ?',
      whereArgs: [studentId],
      orderBy: 'timestamp DESC',
    );

    return List.generate(maps.length, (i) => AttendanceRecord.fromMap(maps[i]));
  }
  
  // --- Timetable Operations ---
  
  Future<List<Map<String, dynamic>>> getTimetable(String day) async {
    final db = await database;
    return await db.query(
      'timetable',
      where: 'day_of_week = ?',
      whereArgs: [day],
      orderBy: 'time_slot ASC',
    );
  }
}
