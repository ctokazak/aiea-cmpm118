% Task 4: knowledge base of UCSC-style CS courses, prerequisites and students.
% 26 facts, 5 rules (two are recursive).

% course(Code, Title)
course(cse20,  'Beginning Programming in Python').
course(cse30,  'Programming Abstractions').
course(cse12,  'Computer Systems and Assembly').
course(cse13s, 'Computer Systems and C Programming').
course(cse16,  'Applied Discrete Mathematics').
course(cse101, 'Data Structures and Algorithms').
course(cse130, 'Principles of Computer Systems Design').
course(cse140, 'Artificial Intelligence').

% prereq(Course, Prerequisite): Prerequisite must be passed before Course.
prereq(cse30,  cse20).
prereq(cse12,  cse20).
prereq(cse13s, cse12).
prereq(cse101, cse30).
prereq(cse101, cse13s).
prereq(cse101, cse16).
prereq(cse130, cse101).
prereq(cse140, cse101).

% passed(Student, Course)
passed(colby, cse20).
passed(colby, cse30).
passed(colby, cse12).
passed(colby, cse13s).
passed(colby, cse16).
passed(maya,  cse20).
passed(maya,  cse12).
passed(maya,  cse16).
passed(jordan, cse20).
passed(jordan, cse30).

% requires(C, P): P is a direct or indirect prerequisite of C.
requires(C, P) :- prereq(C, P).
requires(C, P) :- prereq(C, Mid), requires(Mid, P).

% missing(S, C, P): student S has not passed prerequisite P of course C.
missing(S, C, P) :- prereq(C, P), \+ passed(S, P).

% can_take(S, C): S has passed every direct prerequisite of C and hasn't taken C yet.
can_take(S, C) :-
    student(S), course(C, _),
    \+ passed(S, C),
    \+ missing(S, C, _).

% student(S): anyone who has passed at least one course.
student(S) :- setof(S0, C^passed(S0, C), Students), member(S, Students).

% depth(C, D): length of the longest prerequisite chain below C.
depth(C, 0) :- course(C, _), \+ prereq(C, _).
depth(C, D) :-
    course(C, _), prereq(C, _),
    aggregate_all(max(D0), (prereq(C, P), depth(P, D0)), Max),
    D is Max + 1.
