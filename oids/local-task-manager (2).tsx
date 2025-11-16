import React, { useState, useEffect } from 'react';
import { Plus, Search, User, Calendar, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const TaskManager = () => {
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [activeView, setActiveView] = useState('board');
  const [activePage, setActivePage] = useState('main');
  const [selectedProject, setSelectedProject] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [completedSearchTerm, setCompletedSearchTerm] = useState('');
  const [completedFilterAssignee, setCompletedFilterAssignee] = useState('all');
  const [completedSortBy, setCompletedSortBy] = useState('completedDate');
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);

  const defaultStatuses = [
    { id: 'backlog', name: 'Беклог', color: 'bg-gray-500', icon: AlertCircle },
    { id: 'todo', name: 'До виконання', color: 'bg-blue-500', icon: Clock },
    { id: 'in_progress', name: 'В роботі', color: 'bg-yellow-500', icon: Clock },
    { id: 'review', name: 'На перевірці', color: 'bg-purple-500', icon: AlertCircle },
    { id: 'done', name: 'Виконано', color: 'bg-green-500', icon: CheckCircle }
  ];

  const priorities = [
    { id: 'low', name: 'Низький', color: 'text-gray-600' },
    { id: 'medium', name: 'Середній', color: 'text-yellow-600' },
    { id: 'high', name: 'Високий', color: 'text-orange-600' },
    { id: 'critical', name: 'Критичний', color: 'text-red-600' }
  ];

  const isOverdue = (dueDate) => {
    if (!dueDate) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    return due < today;
  };

  const isDueToday = (dueDate) => {
    if (!dueDate) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    return due.getTime() === today.getTime();
  };

  const isCompletedMoreThan24Hours = (task) => {
    if (task.status !== 'done' && !statuses.find(s => s.id === task.status && s.name === 'Виконано')) return false;
    const now = new Date();
    const updated = new Date(task.updatedAt);
    const hoursDiff = (now - updated) / (1000 * 60 * 60);
    return hoursDiff > 24;
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const projectsData = await window.storage.get('projects');
      const tasksData = await window.storage.get('tasks');
      const usersData = await window.storage.get('users');
      const statusesData = await window.storage.get('statuses');

      if (projectsData) setProjects(JSON.parse(projectsData.value));
      if (tasksData) setTasks(JSON.parse(tasksData.value));
      if (usersData) setUsers(JSON.parse(usersData.value));
      if (statusesData) {
        setStatuses(JSON.parse(statusesData.value));
      } else {
        setStatuses(defaultStatuses);
      }
    } catch (error) {
      setProjects([]);
      setTasks([]);
      setUsers([]);
      setStatuses(defaultStatuses);
    }
  };

  const saveProjects = async (newProjects) => {
    setProjects(newProjects);
    await window.storage.set('projects', JSON.stringify(newProjects));
  };

  const saveTasks = async (newTasks) => {
    setTasks(newTasks);
    await window.storage.set('tasks', JSON.stringify(newTasks));
  };

  const saveUsers = async (newUsers) => {
    setUsers(newUsers);
    await window.storage.set('users', JSON.stringify(newUsers));
  };

  const saveStatuses = async (newStatuses) => {
    setStatuses(newStatuses);
    await window.storage.set('statuses', JSON.stringify(newStatuses));
  };

  const ProjectModal = ({ onClose }) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [key, setKey] = useState('');

    const handleSubmit = async () => {
      if (!name.trim() || !key.trim()) {
        alert('Будь ласка, заповніть всі обов\'язкові поля');
        return;
      }
      try {
        const newProject = {
          id: Date.now().toString(),
          name: name.trim(),
          description: description.trim(),
          key: key.trim().toUpperCase(),
          createdAt: new Date().toISOString()
        };
        await saveProjects([...projects, newProject]);
        onClose();
      } catch (error) {
        console.error('Помилка при створенні проєкту:', error);
        alert('Помилка при створенні проєкту');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">Новий проєкт</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Назва проєкту</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Ключ проєкту (наприклад, PROJ)</label>
              <input
                type="text"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                className="w-full border rounded px-3 py-2 uppercase"
                maxLength={6}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Опис</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full border rounded px-3 py-2"
                rows={3}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 border rounded hover:bg-gray-100"
              >
                Скасувати
              </button>
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Створити
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const TaskModal = ({ onClose, editTask = null }) => {
    const [title, setTitle] = useState(editTask?.title || '');
    const [description, setDescription] = useState(editTask?.description || '');
    const [status, setStatus] = useState(editTask?.status || 'backlog');
    const [priority, setPriority] = useState(editTask?.priority || 'medium');
    const [department, setDepartment] = useState(editTask?.department || '');
    const [assignee, setAssignee] = useState(editTask?.assignee || '');
    const [dueDate, setDueDate] = useState(editTask?.dueDate || '');

    const departments = [
      { id: 'management', name: 'Управління' },
      { id: 'iarm', name: 'ІАРМ' },
      { id: 'sd_ktk', name: 'СД КТК' },
      { id: 'zbsi', name: 'ЗБСІ' },
      { id: 'workshop', name: 'Майстерня' }
    ];

    const handleSubmit = async () => {
      if (!title.trim()) {
        alert('Будь ласка, введіть назву задачі');
        return;
      }
      if (!selectedProject) {
        alert('Будь ласка, оберіть проєкт');
        return;
      }

      try {
        if (editTask) {
          const updatedTasks = tasks.map(t =>
            t.id === editTask.id
              ? { ...t, title: title.trim(), description: description.trim(), status, priority, department, assignee, dueDate, updatedAt: new Date().toISOString() }
              : t
          );
          await saveTasks(updatedTasks);
        } else {
          const taskNumber = tasks.filter(t => t.projectId === selectedProject.id).length + 1;
          const taskKey = `${selectedProject.key}-${taskNumber}`;
          const newTask = {
            id: Date.now().toString(),
            key: taskKey,
            title: title.trim(),
            description: description.trim(),
            status,
            priority,
            department,
            assignee,
            dueDate,
            projectId: selectedProject.id,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          };
          await saveTasks([...tasks, newTask]);
        }
        onClose();
      } catch (error) {
        console.error('Помилка при збереженні задачі:', error);
        alert('Помилка при збереженні задачі');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">{editTask ? 'Редагувати задачу' : 'Нова задача'}</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Назва задачі</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Опис</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full border rounded px-3 py-2"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Статус</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  {statuses.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Пріоритет</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  {priorities.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Підрозділ (необов'язково)</label>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">Не обрано</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Виконавець (необов'язково)</label>
                <select
                  value={assignee}
                  onChange={(e) => setAssignee(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">Не призначено</option>
                  {users.map(u => (
                    <option key={u.id} value={u.id}>{u.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Термін виконання</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 border rounded hover:bg-gray-100"
              >
                Скасувати
              </button>
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                {editTask ? 'Зберегти' : 'Створити'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const UserModal = ({ onClose }) => {
    const [name, setName] = useState('');
    const [surname, setSurname] = useState('');
    const [role, setRole] = useState('management');

    const roles = [
      { id: 'management', name: 'Управління' },
      { id: 'iarm', name: 'ІАРМ' },
      { id: 'sd_ktk', name: 'СД КТК' },
      { id: 'zbsi', name: 'ЗБСІ' },
      { id: 'workshop', name: 'Майстерня' }
    ];

    const handleSubmit = async () => {
      if (!name.trim()) {
        alert('Будь ласка, введіть ім\'я');
        return;
      }
      try {
        const newUser = {
          id: Date.now().toString(),
          name: name.trim(),
          surname: surname.trim(),
          role,
          createdAt: new Date().toISOString()
        };
        await saveUsers([...users, newUser]);
        onClose();
      } catch (error) {
        console.error('Помилка при додаванні користувача:', error);
        alert('Помилка при додаванні користувача');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">Додати користувача</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Ім'я</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Прізвище (необов'язково)</label>
              <input
                type="text"
                value={surname}
                onChange={(e) => setSurname(e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Підрозділ</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full border rounded px-3 py-2"
              >
                {roles.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 border rounded hover:bg-gray-100"
              >
                Скасувати
              </button>
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Додати
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const StatusModal = ({ onClose, editStatus = null }) => {
    const [name, setName] = useState(editStatus?.name || '');
    const [color, setColor] = useState(editStatus?.color || 'bg-blue-500');

    const colors = [
      { id: 'bg-gray-500', name: 'Сірий' },
      { id: 'bg-blue-500', name: 'Синій' },
      { id: 'bg-green-500', name: 'Зелений' },
      { id: 'bg-yellow-500', name: 'Жовтий' },
      { id: 'bg-orange-500', name: 'Помаранчевий' },
      { id: 'bg-red-500', name: 'Червоний' },
      { id: 'bg-purple-500', name: 'Фіолетовий' },
      { id: 'bg-pink-500', name: 'Рожевий' },
      { id: 'bg-indigo-500', name: 'Індиго' },
      { id: 'bg-teal-500', name: 'Бірюзовий' }
    ];

    const handleSubmit = async () => {
      if (!name.trim()) {
        alert('Будь ласка, введіть назву статусу');
        return;
      }
      try {
        if (editStatus) {
          const updatedStatuses = statuses.map(s =>
            s.id === editStatus.id
              ? { ...s, name: name.trim(), color }
              : s
          );
          await saveStatuses(updatedStatuses);
        } else {
          const newStatus = {
            id: Date.now().toString(),
            name: name.trim(),
            color,
            icon: Clock,
            createdAt: new Date().toISOString()
          };
          await saveStatuses([...statuses, newStatus]);
        }
        onClose();
      } catch (error) {
        console.error('Помилка при збереженні статусу:', error);
        alert('Помилка при збереженні статусу');
      }
    };

    const handleDelete = async () => {
      if (!editStatus) return;
      if (!confirm('Ви впевнені, що хочете видалити цей статус? Задачі з цим статусом будуть переміщені в "Беклог".')) return;
      
      try {
        const updatedStatuses = statuses.filter(s => s.id !== editStatus.id);
        await saveStatuses(updatedStatuses);
        
        const updatedTasks = tasks.map(t =>
          t.status === editStatus.id ? { ...t, status: 'backlog' } : t
        );
        await saveTasks(updatedTasks);
        
        onClose();
      } catch (error) {
        console.error('Помилка при видаленні статусу:', error);
        alert('Помилка при видаленні статусу');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">{editStatus ? 'Редагувати статус' : 'Новий статус'}</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Назва статусу</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Колір</label>
              <div className="grid grid-cols-5 gap-2">
                {colors.map(c => (
                  <button
                    key={c.id}
                    onClick={() => setColor(c.id)}
                    className={`h-10 rounded ${c.id} ${color === c.id ? 'ring-2 ring-offset-2 ring-blue-600' : ''}`}
                    title={c.name}
                  />
                ))}
              </div>
            </div>
            <div className="flex gap-2 justify-between">
              {editStatus && (
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Видалити
                </button>
              )}
              <div className="flex gap-2 ml-auto">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  Скасувати
                </button>
                <button
                  onClick={handleSubmit}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {editStatus ? 'Зберегти' : 'Створити'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const TaskCard = ({ task, onEdit }) => {
    const status = statuses.find(s => s.id === task.status);
    const priority = priorities.find(p => p.id === task.priority);
    const assignedUser = users.find(u => u.id === task.assignee);
    const departments = [
      { id: 'management', name: 'Управління' },
      { id: 'iarm', name: 'ІАРМ' },
      { id: 'sd_ktk', name: 'СД КТК' },
      { id: 'zbsi', name: 'ЗБСІ' },
      { id: 'workshop', name: 'Майстерня' }
    ];
    const taskDepartment = departments.find(d => d.id === task.department);
    const overdue = isOverdue(task.dueDate);
    const dueToday = isDueToday(task.dueDate);

    const handleDragStart = (e) => {
      e.dataTransfer.setData('taskId', task.id);
    };

    let cardBorderClass = 'border';
    if (overdue && task.status !== 'done') {
      cardBorderClass = 'border-2 border-red-500 shadow-red-100';
    } else if (dueToday && task.status !== 'done') {
      cardBorderClass = 'border-2 border-orange-500 shadow-orange-100';
    }

    return (
      <div
        draggable
        onDragStart={handleDragStart}
        onClick={() => onEdit(task)}
        className={`bg-white ${cardBorderClass} rounded-lg p-3 mb-2 cursor-pointer hover:shadow-md transition-shadow`}
      >
        <div className="flex items-start justify-between mb-2">
          <span className="text-xs font-mono text-gray-500">{task.key}</span>
          <span className={`text-xs font-medium ${priority.color}`}>
            {priority.name}
          </span>
        </div>
        <h4 className="font-medium text-sm mb-2">{task.title}</h4>
        {task.description && (
          <p className="text-xs text-gray-600 mb-2 line-clamp-2">{task.description}</p>
        )}
        {taskDepartment && (
          <div className="text-xs text-blue-600 mb-2 font-medium">
            {taskDepartment.name}
          </div>
        )}
        <div className="flex items-center justify-between text-xs text-gray-500">
          {assignedUser && (
            <div className="flex items-center gap-1">
              <User size={12} />
              <span>{assignedUser.name}</span>
            </div>
          )}
          {task.dueDate && (
            <div className={`flex items-center gap-1 ${overdue ? 'text-red-600 font-bold' : dueToday ? 'text-orange-600 font-bold' : ''}`}>
              <Calendar size={12} />
              <span>{new Date(task.dueDate).toLocaleDateString('uk-UA')}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const BoardView = () => {
    const projectTasks = tasks.filter(t => t.projectId === selectedProject?.id);
    const activeTasks = projectTasks.filter(task => !isCompletedMoreThan24Hours(task));
    const filteredTasks = activeTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          task.key.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || task.status === filterStatus;
      return matchesSearch && matchesStatus;
    });

    const handleDrop = async (e, newStatus) => {
      e.preventDefault();
      const taskId = e.dataTransfer.getData('taskId');
      const updatedTasks = tasks.map(t =>
        t.id === taskId ? { ...t, status: newStatus, updatedAt: new Date().toISOString() } : t
      );
      await saveTasks(updatedTasks);
    };

    const handleDragOver = (e) => {
      e.preventDefault();
    };

    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {statuses.map(status => {
          const statusTasks = filteredTasks.filter(t => t.status === status.id);
          
          return (
            <div
              key={status.id}
              onDrop={(e) => handleDrop(e, status.id)}
              onDragOver={handleDragOver}
              className="flex-shrink-0 w-72 bg-gray-50 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${status.color}`} />
                  <h3 className="font-semibold text-sm">{status.name}</h3>
                  <span className="text-xs text-gray-500 bg-white px-2 py-0.5 rounded-full">
                    {statusTasks.length}
                  </span>
                </div>
                <button
                  onClick={() => setShowStatusModal(status)}
                  className="text-gray-400 hover:text-gray-600"
                  title="Редагувати статус"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
              </div>
              <div className="space-y-2">
                {statusTasks.map(task => (
                  <TaskCard key={task.id} task={task} onEdit={(t) => setShowTaskModal(t)} />
                ))}
              </div>
            </div>
          );
        })}
        <div className="flex-shrink-0 w-72">
          <button
            onClick={() => setShowStatusModal(true)}
            className="w-full h-32 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex items-center justify-center text-gray-500 hover:text-blue-600"
          >
            <div className="text-center">
              <Plus size={24} className="mx-auto mb-1" />
              <span className="text-sm font-medium">Додати статус</span>
            </div>
          </button>
        </div>
      </div>
    );
  };

  const ListView = () => {
    const projectTasks = tasks.filter(t => t.projectId === selectedProject?.id);
    const activeTasks = projectTasks.filter(task => !isCompletedMoreThan24Hours(task));
    const filteredTasks = activeTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          task.key.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || task.status === filterStatus;
      return matchesSearch && matchesStatus;
    });

    const departments = [
      { id: 'management', name: 'Управління' },
      { id: 'iarm', name: 'ІАРМ' },
      { id: 'sd_ktk', name: 'СД КТК' },
      { id: 'zbsi', name: 'ЗБСІ' },
      { id: 'workshop', name: 'Майстерня' }
    ];

    return (
      <div className="bg-white rounded-lg border overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Ключ</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Назва</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Підрозділ</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Пріоритет</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Виконавець</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Термін</th>
            </tr>
          </thead>
          <tbody>
            {filteredTasks.map(task => {
              const status = statuses.find(s => s.id === task.status);
              const priority = priorities.find(p => p.id === task.priority);
              const assignedUser = users.find(u => u.id === task.assignee);
              const taskDepartment = departments.find(d => d.id === task.department);
              const overdue = isOverdue(task.dueDate);
              const dueToday = isDueToday(task.dueDate);
              
              return (
                <tr
                  key={task.id}
                  onClick={() => setShowTaskModal(task)}
                  className={`border-b hover:bg-gray-50 cursor-pointer ${overdue && task.status !== 'done' ? 'bg-red-50' : dueToday && task.status !== 'done' ? 'bg-orange-50' : ''}`}
                >
                  <td className="px-4 py-3 text-sm font-mono text-gray-600">{task.key}</td>
                  <td className="px-4 py-3 text-sm">{task.title}</td>
                  <td className="px-4 py-3 text-sm">
                    {taskDepartment ? (
                      <span className="text-blue-600 font-medium">{taskDepartment.name}</span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs text-white ${status.color}`}>
                      {status.name}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-medium ${priority.color}`}>
                      {priority.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {assignedUser ? assignedUser.name : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {task.dueDate ? (
                      <span className={overdue ? 'text-red-600 font-bold' : dueToday ? 'text-orange-600 font-bold' : ''}>
                        {new Date(task.dueDate).toLocaleDateString('uk-UA')}
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filteredTasks.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Задач не знайдено
          </div>
        )}
      </div>
    );
  };

  const CompletedTasksPage = () => {
    const allCompletedTasks = tasks.filter(task => {
      const isDone = task.status === 'done' || statuses.find(s => s.id === task.status && s.name === 'Виконано');
      return isDone;
    });

    const filteredCompleted = allCompletedTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(completedSearchTerm.toLowerCase()) ||
                          task.description.toLowerCase().includes(completedSearchTerm.toLowerCase()) ||
                          task.key.toLowerCase().includes(completedSearchTerm.toLowerCase());
      const matchesAssignee = completedFilterAssignee === 'all' || task.assignee === completedFilterAssignee;
      return matchesSearch && matchesAssignee;
    });

    const sortedTasks = [...filteredCompleted].sort((a, b) => {
      if (completedSortBy === 'completedDate') {
        return new Date(b.updatedAt) - new Date(a.updatedAt);
      } else if (completedSortBy === 'title') {
        return a.title.localeCompare(b.title);
      } else if (completedSortBy === 'assignee') {
        const userA = users.find(u => u.id === a.assignee);
        const userB = users.find(u => u.id === b.assignee);
        const nameA = userA ? userA.name : '';
        const nameB = userB ? userB.name : '';
        return nameA.localeCompare(nameB);
      }
      return 0;
    });

    const departments = [
      { id: 'management', name: 'Управління' },
      { id: 'iarm', name: 'ІАРМ' },
      { id: 'sd_ktk', name: 'СД КТК' },
      { id: 'zbsi', name: 'ЗБСІ' },
      { id: 'workshop', name: 'Майстерня' }
    ];

    return (
      <div>
        <div className="bg-white rounded-lg p-4 mb-6 shadow-sm">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Пошук по назві, опису, ключу..."
                value={completedSearchTerm}
                onChange={(e) => setCompletedSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded"
              />
            </div>
            <select
              value={completedFilterAssignee}
              onChange={(e) => setCompletedFilterAssignee(e.target.value)}
              className="border rounded px-3 py-2"
            >
              <option value="all">Всі виконавці</option>
              {users.map(u => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
            <select
              value={completedSortBy}
              onChange={(e) => setCompletedSortBy(e.target.value)}
              className="border rounded px-3 py-2"
            >
              <option value="completedDate">За датою виконання</option>
              <option value="title">За назвою</option>
              <option value="assignee">За виконавцем</option>
            </select>
          </div>
        </div>

        <div className="bg-white rounded-lg border overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Ключ</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Назва</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Підрозділ</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Виконавець</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Дата виконання</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Проєкт</th>
              </tr>
            </thead>
            <tbody>
              {sortedTasks.map(task => {
                const assignedUser = users.find(u => u.id === task.assignee);
                const taskDepartment = departments.find(d => d.id === task.department);
                const project = projects.find(p => p.id === task.projectId);
                
                return (
                  <tr
                    key={task.id}
                    onClick={() => setShowTaskModal(task)}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-4 py-3 text-sm font-mono text-gray-600">{task.key}</td>
                    <td className="px-4 py-3 text-sm">{task.title}</td>
                    <td className="px-4 py-3 text-sm">
                      {taskDepartment ? (
                        <span className="text-blue-600 font-medium">{taskDepartment.name}</span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {assignedUser ? assignedUser.name : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {new Date(task.updatedAt).toLocaleString('uk-UA')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {project ? project.name : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {sortedTasks.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              Виконаних задач не знайдено
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">TaskFlow</h1>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActivePage('main')}
                className={`px-3 py-2 text-sm rounded ${activePage === 'main' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
              >
                Активні задачі
              </button>
              <button
                onClick={() => setActivePage('completed')}
                className={`px-3 py-2 text-sm rounded ${activePage === 'completed' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
              >
                Виконані задачі
              </button>
              <button
                onClick={() => setShowUserModal(true)}
                className="px-3 py-2 text-sm border rounded hover:bg-gray-50 flex items-center gap-2"
              >
                <User size={16} />
                Користувачі
              </button>
              <button
                onClick={() => setShowProjectModal(true)}
                className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
              >
                <Plus size={16} />
                Новий проєкт
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activePage === 'completed' ? (
          <CompletedTasksPage />
        ) : (
          <>
            {/* Project Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Оберіть проєкт</label>
              <select
                value={selectedProject?.id || ''}
                onChange={(e) => setSelectedProject(projects.find(p => p.id === e.target.value))}
                className="w-full max-w-md border rounded px-3 py-2"
              >
                <option value="">— Оберіть проєкт —</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name} ({p.key})</option>
                ))}
              </select>
            </div>

            {selectedProject && (
              <>
                {/* Toolbar */}
                <div className="bg-white rounded-lg p-4 mb-6 shadow-sm">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setActiveView('board')}
                        className={`px-4 py-2 rounded ${activeView === 'board' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
                      >
                        Дошка
                      </button>
                      <button
                        onClick={() => setActiveView('list')}
                        className={`px-4 py-2 rounded ${activeView === 'list' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
                      >
                        Список
                      </button>
                    </div>

                    <div className="flex items-center gap-2 flex-1 max-w-2xl">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                        <input
                          type="text"
                          placeholder="Пошук задач..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 border rounded"
                        />
                      </div>
                      <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="border rounded px-3 py-2"
                      >
                        <option value="all">Всі статуси</option>
                        {statuses.map(s => (
                          <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                      </select>
                    </div>

                    <button
                      onClick={() => setShowTaskModal(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
                    >
                      <Plus size={16} />
                      Створити задачу
                    </button>
                  </div>
                </div>

                {/* Views */}
                {activeView === 'board' ? <BoardView /> : <ListView />}
              </>
            )}

            {!selectedProject && projects.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-4">Створіть свій перший проєкт для початку роботи</p>
                <button
                  onClick={() => setShowProjectModal(true)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Створити проєкт
                </button>
              </div>
            )}

            {!selectedProject && projects.length > 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500">Оберіть проєкт зі списку вище</p>
              </div>
            )}
          </>
        )}
      </main>

      {/* Modals */}
      {showProjectModal && <ProjectModal onClose={() => setShowProjectModal(false)} />}
      {showTaskModal && (
        <TaskModal
          onClose={() => setShowTaskModal(false)}
          editTask={typeof showTaskModal === 'object' ? showTaskModal : null}
        />
      )}
      {showUserModal && <UserModal onClose={() => setShowUserModal(false)} />}
      {showStatusModal && (
        <StatusModal
          onClose={() => setShowStatusModal(false)}
          editStatus={typeof showStatusModal === 'object' ? showStatusModal : null}
        />
      )}
    </div>
  );
};

export default TaskManager;