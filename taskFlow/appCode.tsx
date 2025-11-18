import React, { useState, useEffect } from 'react';
import { Plus, Search, User, Calendar, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const TaskManager = () => {
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [departments, setDepartments] = useState([]);
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
  const [showProjectManageModal, setShowProjectManageModal] = useState(false);
  const [showUserManageModal, setShowUserManageModal] = useState(false);
  const [showDepartmentModal, setShowDepartmentModal] = useState(false);

  const defaultStatuses = [
    { id: 'backlog', name: 'Беклог', color: 'bg-gray-500' },
    { id: 'todo', name: 'До виконання', color: 'bg-blue-500' },
    { id: 'in_progress', name: 'В роботі', color: 'bg-yellow-500' },
    { id: 'review', name: 'На перевірці', color: 'bg-purple-500' },
    { id: 'done', name: 'Виконано', color: 'bg-green-500' }
  ];

  const priorities = [
    { id: 'low', name: 'Низький', color: 'text-gray-600' },
    { id: 'medium', name: 'Середній', color: 'text-yellow-600' },
    { id: 'high', name: 'Високий', color: 'text-orange-600' },
    { id: 'critical', name: 'Критичний', color: 'text-red-600' }
  ];

  const defaultDepartments = [
    { id: 'management', name: 'Управління' },
    { id: 'iarm', name: 'ІАРМ' },
    { id: 'sd_ktk', name: 'СД КТК' },
    { id: 'zbsi', name: 'ЗБСІ' },
    { id: 'workshop', name: 'Майстерня' }
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
    const doneStatus = statuses.find(s => s.id === task.status);
    const taskProject = projects.find(p => p.id === task.projectId);
    const projectDoneStatus = taskProject?.customStatuses?.find(s => s.id === task.status);
    
    const isDone = doneStatus?.name === 'Виконано' || projectDoneStatus?.name === 'Виконано';
    if (!isDone) return false;
    
    const updated = new Date(task.updatedAt);
    const nextDay = new Date(updated);
    nextDay.setDate(nextDay.getDate() + 1);
    nextDay.setHours(8, 5, 0, 0);
    
    const now = new Date();
    return now >= nextDay;
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
      const departmentsData = await window.storage.get('departments');

      if (projectsData) setProjects(JSON.parse(projectsData.value));
      if (tasksData) setTasks(JSON.parse(tasksData.value));
      if (usersData) setUsers(JSON.parse(usersData.value));
      if (statusesData) {
        setStatuses(JSON.parse(statusesData.value));
      } else {
        setStatuses(defaultStatuses);
      }
      if (departmentsData) {
        setDepartments(JSON.parse(departmentsData.value));
      } else {
        setDepartments(defaultDepartments);
      }
    } catch (error) {
      setProjects([]);
      setTasks([]);
      setUsers([]);
      setStatuses(defaultStatuses);
      setDepartments(defaultDepartments);
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

  const saveDepartments = async (newDepartments) => {
    setDepartments(newDepartments);
    await window.storage.set('departments', JSON.stringify(newDepartments));
  };

  const ProjectModal = ({ onClose, editProject = null }) => {
    const [name, setName] = useState(editProject?.name || '');
    const [description, setDescription] = useState(editProject?.description || '');
    const [key, setKey] = useState(editProject?.key || '');
    const [useCustomStatuses, setUseCustomStatuses] = useState(!!editProject?.customStatuses || false);

    const handleSubmit = async () => {
      if (!name.trim() || !key.trim()) {
        alert('Заповніть всі поля');
        return;
      }
      try {
        if (editProject) {
          const updatedProjects = projects.map(p =>
            p.id === editProject.id
              ? { ...p, name: name.trim(), description: description.trim(), customStatuses: useCustomStatuses ? (p.customStatuses || JSON.parse(JSON.stringify(statuses))) : null }
              : p
          );
          await saveProjects(updatedProjects);
          if (selectedProject?.id === editProject.id) {
            setSelectedProject(updatedProjects.find(p => p.id === editProject.id));
          }
        } else {
          const newProject = {
            id: Date.now().toString(),
            name: name.trim(),
            description: description.trim(),
            key: key.trim().toUpperCase(),
            customStatuses: useCustomStatuses ? JSON.parse(JSON.stringify(statuses)) : null,
            createdAt: new Date().toISOString()
          };
          await saveProjects([...projects, newProject]);
        }
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    const handleDelete = async () => {
      if (!editProject) return;
      if (!confirm('Видалити проєкт?')) return;
      
      try {
        await saveProjects(projects.filter(p => p.id !== editProject.id));
        await saveTasks(tasks.filter(t => t.projectId !== editProject.id));
        if (selectedProject?.id === editProject.id) {
          setSelectedProject(null);
        }
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">{editProject ? 'Редагувати' : 'Новий проєкт'}</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Назва</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Ключ</label>
              <input type="text" value={key} onChange={(e) => setKey(e.target.value)} className="w-full border rounded px-3 py-2 uppercase" maxLength={6} disabled={!!editProject} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Опис</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border rounded px-3 py-2" rows={3} />
            </div>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={useCustomStatuses} onChange={(e) => setUseCustomStatuses(e.target.checked)} />
              <span className="text-sm">Власні статуси</span>
            </label>
            <div className="flex gap-2 justify-between">
              {editProject && <button onClick={handleDelete} className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Видалити</button>}
              <div className="flex gap-2 ml-auto">
                <button onClick={onClose} className="px-4 py-2 border rounded">Скасувати</button>
                <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">Зберегти</button>
              </div>
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

    const taskProject = editTask ? projects.find(p => p.id === editTask.projectId) : selectedProject !== 'all' ? selectedProject : null;
    const availableStatuses = taskProject?.customStatuses || statuses;

    const handleSubmit = async () => {
      if (!title.trim() || !taskProject) {
        alert('Заповніть назву');
        return;
      }

      try {
        if (editTask) {
          await saveTasks(tasks.map(t =>
            t.id === editTask.id ? { ...t, title: title.trim(), description: description.trim(), status, priority, department, assignee, dueDate, updatedAt: new Date().toISOString() } : t
          ));
        } else {
          const taskNumber = tasks.filter(t => t.projectId === taskProject.id).length + 1;
          const newTask = {
            id: Date.now().toString(),
            key: `${taskProject.key}-${taskNumber}`,
            title: title.trim(),
            description: description.trim(),
            status,
            priority,
            department,
            assignee,
            dueDate,
            projectId: taskProject.id,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          };
          await saveTasks([...tasks, newTask]);
        }
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    const handleDelete = async () => {
      if (!editTask || !confirm('Видалити задачу?')) return;
      try {
        await saveTasks(tasks.filter(t => t.id !== editTask.id));
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">{editTask ? 'Редагувати' : 'Нова задача'}</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Назва</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full border rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Опис</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border rounded px-3 py-2" rows={4} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Статус</label>
                <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full border rounded px-3 py-2">
                  {availableStatuses.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Пріоритет</label>
                <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full border rounded px-3 py-2">
                  {priorities.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Підрозділ</label>
                <select value={department} onChange={(e) => setDepartment(e.target.value)} className="w-full border rounded px-3 py-2">
                  <option value="">Не обрано</option>
                  {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Виконавець</label>
                <select value={assignee} onChange={(e) => setAssignee(e.target.value)} className="w-full border rounded px-3 py-2">
                  <option value="">Не призначено</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Термін</label>
              <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full border rounded px-3 py-2" />
            </div>
            <div className="flex gap-2 justify-between">
              {editTask && <button onClick={handleDelete} className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Видалити</button>}
              <div className="flex gap-2 ml-auto">
                <button onClick={onClose} className="px-4 py-2 border rounded">Скасувати</button>
                <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">Зберегти</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const UserModal = ({ onClose, editUser = null }) => {
    const [name, setName] = useState(editUser?.name || '');
    const [surname, setSurname] = useState(editUser?.surname || '');
    const [role, setRole] = useState(editUser?.role || 'management');

    const handleSubmit = async () => {
      if (!name.trim()) {
        alert('Введіть ім\'я');
        return;
      }
      try {
        if (editUser) {
          await saveUsers(users.map(u => u.id === editUser.id ? { ...u, name: name.trim(), surname: surname.trim(), role } : u));
        } else {
          await saveUsers([...users, { id: Date.now().toString(), name: name.trim(), surname: surname.trim(), role, createdAt: new Date().toISOString() }]);
        }
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    const handleDelete = async () => {
      if (!editUser || !confirm('Видалити?')) return;
      try {
        await saveUsers(users.filter(u => u.id !== editUser.id));
        await saveTasks(tasks.map(t => t.assignee === editUser.id ? { ...t, assignee: '' } : t));
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">{editUser ? 'Редагувати' : 'Новий користувач'}</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Ім'я</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Прізвище</label>
              <input type="text" value={surname} onChange={(e) => setSurname(e.target.value)} className="w-full border rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Підрозділ</label>
              <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full border rounded px-3 py-2">
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div className="flex gap-2 justify-between">
              {editUser && <button onClick={handleDelete} className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Видалити</button>}
              <div className="flex gap-2 ml-auto">
                <button onClick={onClose} className="px-4 py-2 border rounded">Скасувати</button>
                <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">Зберегти</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const StatusModal = ({ onClose, editStatus = null }) => {
    const [name, setName] = useState(editStatus?.name || '');
    const [color, setColor] = useState(editStatus?.color || 'bg-blue-500');
    const [statusOrder, setStatusOrder] = useState([]);

    const colors = [
      'bg-gray-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-orange-500',
      'bg-red-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500'
    ];

    const isProjectSpecific = selectedProject && selectedProject !== 'all' && selectedProject.customStatuses;
    const currentStatuses = isProjectSpecific ? selectedProject.customStatuses : statuses;

    useEffect(() => {
      setStatusOrder([...currentStatuses]);
    }, []);

    const moveStatus = (index, direction) => {
      const newOrder = [...statusOrder];
      const newIndex = direction === 'up' ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= newOrder.length) return;
      const temp = newOrder[index];
      newOrder[index] = newOrder[newIndex];
      newOrder[newIndex] = temp;
      setStatusOrder(newOrder);
    };

    const handleSubmit = async () => {
      if (!editStatus && !name.trim()) {
        alert('Введіть назву');
        return;
      }
      
      try {
        let updatedStatuses = editStatus 
          ? statusOrder.map(s => s.id === editStatus.id ? { ...s, name: name.trim(), color } : s)
          : [...statusOrder, { id: Date.now().toString(), name: name.trim(), color, createdAt: new Date().toISOString() }];

        if (isProjectSpecific) {
          await saveProjects(projects.map(p => p.id === selectedProject.id ? { ...p, customStatuses: updatedStatuses } : p));
          setSelectedProject({ ...selectedProject, customStatuses: updatedStatuses });
        } else {
          await saveStatuses(updatedStatuses);
        }
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    const handleDelete = async () => {
      if (!editStatus || !confirm('Видалити?')) return;
      
      try {
        const updatedStatusList = statusOrder.filter(s => s.id !== editStatus.id);
        const fallback = updatedStatusList[0]?.id || 'backlog';

        if (isProjectSpecific) {
          await saveProjects(projects.map(p => p.id === selectedProject.id ? { ...p, customStatuses: updatedStatusList } : p));
          setSelectedProject({ ...selectedProject, customStatuses: updatedStatusList });
          await saveTasks(tasks.map(t => t.projectId === selectedProject.id && t.status === editStatus.id ? { ...t, status: fallback } : t));
        } else {
          await saveStatuses(updatedStatusList);
          await saveTasks(tasks.map(t => t.status === editStatus.id ? { ...t, status: fallback } : t));
        }
        onClose();
      } catch (error) {
        alert('Помилка');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">{editStatus ? 'Редагувати' : 'Новий статус'}</h2>
          {editStatus ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1">Назва</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm mb-1">Колір</label>
                <div className="grid grid-cols-5 gap-2">
                  {colors.map(c => <button key={c} onClick={() => setColor(c)} className={`h-10 rounded ${c} ${color === c ? 'ring-2 ring-blue-600' : ''}`} />)}
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="space-y-4 mb-4">
                <div>
                  <label className="block text-sm mb-1">Назва</label>
                  <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-2" />
                </div>
                <div>
                  <label className="block text-sm mb-1">Колір</label>
                  <div className="grid grid-cols-5 gap-2">
                    {colors.map(c => <button key={c} onClick={() => setColor(c)} className={`h-10 rounded ${c} ${color === c ? 'ring-2 ring-blue-600' : ''}`} />)}
                  </div>
                </div>
              </div>
              <div className="border-t pt-4">
                <label className="block text-sm mb-2">Порядок</label>
                <div className="space-y-2">
                  {statusOrder.map((s, i) => (
                    <div key={s.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <div className={`w-3 h-3 rounded-full ${s.color}`} />
                      <span className="flex-1 text-sm">{s.name}</span>
                      <button onClick={() => moveStatus(i, 'up')} disabled={i === 0} className="p-1 hover:bg-gray-200 rounded disabled:opacity-30">↑</button>
                      <button onClick={() => moveStatus(i, 'down')} disabled={i === statusOrder.length - 1} className="p-1 hover:bg-gray-200 rounded disabled:opacity-30">↓</button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
          <div className="flex gap-2 justify-between mt-4">
            {editStatus && <button onClick={handleDelete} className="px-4 py-2 bg-red-600 text-white rounded">Видалити</button>}
            <div className="flex gap-2 ml-auto">
              <button onClick={onClose} className="px-4 py-2 border rounded">Скасувати</button>
              <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">Зберегти</button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const ProjectManageModal = ({ onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Управління проєктами</h2>
          <button onClick={() => { setShowProjectModal(true); onClose(); }} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            <Plus size={16} className="inline mr-1" />Проєкт
          </button>
        </div>
        <div className="space-y-2">
          {projects.map(project => (
            <div key={project.id} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50">
              <div>
                <div className="font-medium">{project.name}</div>
                <div className="text-sm text-gray-500">{project.key}</div>
              </div>
              <button onClick={() => { setShowProjectModal(project); onClose(); }} className="px-3 py-1 text-sm bg-blue-600 text-white rounded">Редагувати</button>
            </div>
          ))}
        </div>
        <button onClick={onClose} className="mt-4 px-4 py-2 border rounded">Закрити</button>
      </div>
    </div>
  );

  const UserManageModal = ({ onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Управління користувачами</h2>
          <div className="flex gap-2">
            <button onClick={() => { setShowDepartmentModal(true); onClose(); }} className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
              Підрозділи
            </button>
            <button onClick={() => { setShowUserModal(true); onClose(); }} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              <Plus size={16} className="inline mr-1" />Користувача
            </button>
          </div>
        </div>
        <div className="space-y-2">
          {users.map(user => {
            const userRole = departments.find(d => d.id === user.role);
            return (
              <div key={user.id} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50">
                <div>
                  <div className="font-medium">{user.name} {user.surname}</div>
                  <div className="text-sm text-gray-500">{userRole?.name}</div>
                </div>
                <button onClick={() => { setShowUserModal(user); onClose(); }} className="px-3 py-1 text-sm bg-blue-600 text-white rounded">Редагувати</button>
              </div>
            );
          })}
        </div>
        <button onClick={onClose} className="mt-4 px-4 py-2 border rounded">Закрити</button>
      </div>
    </div>
  );

  const DepartmentModal = ({ onClose }) => {
    const [editingDept, setEditingDept] = useState(null);
    const [newDeptName, setNewDeptName] = useState('');

    const handleAdd = async () => {
      if (!newDeptName.trim()) {
        alert('Введіть назву підрозділу');
        return;
      }
      try {
        const newDept = {
          id: Date.now().toString(),
          name: newDeptName.trim(),
          createdAt: new Date().toISOString()
        };
        await saveDepartments([...departments, newDept]);
        setNewDeptName('');
      } catch (error) {
        alert('Помилка');
      }
    };

    const handleUpdate = async (dept, newName) => {
      if (!newName.trim()) {
        alert('Введіть назву підрозділу');
        return;
      }
      try {
        await saveDepartments(departments.map(d => d.id === dept.id ? { ...d, name: newName.trim() } : d));
        setEditingDept(null);
      } catch (error) {
        alert('Помилка');
      }
    };

    const handleDelete = async (dept) => {
      if (!confirm('Видалити підрозділ? Користувачі та задачі з цим підрозділом будуть оновлені.')) return;
      try {
        await saveDepartments(departments.filter(d => d.id !== dept.id));
        await saveUsers(users.map(u => u.role === dept.id ? { ...u, role: '' } : u));
        await saveTasks(tasks.map(t => t.department === dept.id ? { ...t, department: '' } : t));
      } catch (error) {
        alert('Помилка');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">Управління підрозділами</h2>
          
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Додати новий підрозділ</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newDeptName}
                onChange={(e) => setNewDeptName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
                placeholder="Назва підрозділу"
                className="flex-1 border rounded px-3 py-2"
              />
              <button onClick={handleAdd} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                <Plus size={16} className="inline mr-1" />Додати
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium mb-2">Існуючі підрозділи</label>
            {departments.map(dept => (
              <div key={dept.id} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50">
                {editingDept?.id === dept.id ? (
                  <input
                    type="text"
                    defaultValue={dept.name}
                    onBlur={(e) => handleUpdate(dept, e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleUpdate(dept, e.target.value)}
                    autoFocus
                    className="flex-1 border rounded px-2 py-1 mr-2"
                  />
                ) : (
                  <div className="font-medium">{dept.name}</div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingDept(dept)}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Редагувати
                  </button>
                  <button
                    onClick={() => handleDelete(dept)}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Видалити
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button onClick={onClose} className="mt-4 px-4 py-2 border rounded">Закрити</button>
        </div>
      </div>
    );
  };

  const TaskCard = ({ task, onEdit }) => {
    const priority = priorities.find(p => p.id === task.priority);
    const assignedUser = users.find(u => u.id === task.assignee);
    const taskDepartment = departments.find(d => d.id === task.department);
    const overdue = isOverdue(task.dueDate);
    const dueToday = isDueToday(task.dueDate);

    const handleDragStart = (e) => {
      e.dataTransfer.setData('taskId', task.id);
    };

    let cardClass = 'bg-white border rounded-lg p-3 mb-2 cursor-pointer hover:shadow-md transition-shadow';
    if (overdue && task.status !== 'done') cardClass += ' border-red-500 border-2';
    else if (dueToday && task.status !== 'done') cardClass += ' border-orange-500 border-2';

    return (
      <div draggable onDragStart={handleDragStart} onClick={() => onEdit(task)} className={cardClass}>
        <div className="flex items-start justify-between mb-2">
          <span className="text-xs font-mono text-gray-500">{task.key}</span>
          <span className={`text-xs font-medium ${priority.color}`}>{priority.name}</span>
        </div>
        <h4 className="font-medium text-sm mb-2">{task.title}</h4>
        {task.description && <p className="text-xs text-gray-600 mb-2 line-clamp-2">{task.description}</p>}
        {taskDepartment && <div className="text-xs text-blue-600 mb-2 font-medium">{taskDepartment.name}</div>}
        <div className="flex items-center justify-between text-xs text-gray-500">
          {assignedUser && <div className="flex items-center gap-1"><User size={12} /><span>{assignedUser.name}</span></div>}
          {task.dueDate && <div className={`flex items-center gap-1 ${overdue ? 'text-red-600 font-bold' : dueToday ? 'text-orange-600 font-bold' : ''}`}><Calendar size={12} /><span>{new Date(task.dueDate).toLocaleDateString('uk-UA')}</span></div>}
        </div>
      </div>
    );
  };

  const BoardView = () => {
    const currentStatuses = selectedProject === 'all' || !selectedProject?.customStatuses ? statuses : selectedProject.customStatuses;
    let projectTasks = selectedProject === 'all' ? tasks : tasks.filter(t => t.projectId === selectedProject?.id);
    const activeTasks = projectTasks.filter(task => !isCompletedMoreThan24Hours(task));
    const filteredTasks = activeTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) || task.key.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || task.status === filterStatus;
      return matchesSearch && matchesStatus;
    });

    const handleDrop = async (e, newStatus) => {
      e.preventDefault();
      const taskId = e.dataTransfer.getData('taskId');
      await saveTasks(tasks.map(t => t.id === taskId ? { ...t, status: newStatus, updatedAt: new Date().toISOString() } : t));
    };

    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {currentStatuses.map(status => {
          const statusTasks = filteredTasks.filter(t => t.status === status.id);
          return (
            <div key={status.id} onDrop={(e) => handleDrop(e, status.id)} onDragOver={(e) => e.preventDefault()} className="flex-shrink-0 w-72 bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${status.color}`} />
                  <h3 className="font-semibold text-sm">{status.name}</h3>
                  <span className="text-xs text-gray-500 bg-white px-2 py-0.5 rounded-full">{statusTasks.length}</span>
                </div>
                {selectedProject !== 'all' && <button onClick={() => setShowStatusModal(status)} className="text-gray-400 hover:text-gray-600">⋮</button>}
              </div>
              <div className="space-y-2">
                {statusTasks.map(task => <TaskCard key={task.id} task={task} onEdit={(t) => setShowTaskModal(t)} />)}
              </div>
            </div>
          );
        })}
        {selectedProject !== 'all' && (
          <div className="flex-shrink-0 w-72">
            <button onClick={() => setShowStatusModal(true)} className="w-full h-32 border-2 border-dashed rounded-lg hover:border-blue-500 hover:bg-blue-50 flex items-center justify-center text-gray-500">
              <div className="text-center"><Plus size={24} className="mx-auto mb-1" /><span className="text-sm">Додати статус</span></div>
            </button>
          </div>
        )}
      </div>
    );
  };

  const ListView = () => {
    const currentStatuses = selectedProject === 'all' || !selectedProject?.customStatuses ? statuses : selectedProject.customStatuses;
    let projectTasks = selectedProject === 'all' ? tasks : tasks.filter(t => t.projectId === selectedProject?.id);
    const activeTasks = projectTasks.filter(task => !isCompletedMoreThan24Hours(task));
    const filteredTasks = activeTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) || task.key.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || task.status === filterStatus;
      return matchesSearch && matchesStatus;
    });

    return (
      <div className="bg-white rounded-lg border overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Ключ</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Назва</th>
              {selectedProject === 'all' && <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Проєкт</th>}
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Підрозділ</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Пріоритет</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Виконавець</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Термін</th>
            </tr>
          </thead>
          <tbody>
            {filteredTasks.map(task => {
              const status = currentStatuses.find(s => s.id === task.status) || statuses.find(s => s.id === task.status);
              const priority = priorities.find(p => p.id === task.priority);
              const assignedUser = users.find(u => u.id === task.assignee);
              const taskDepartment = departments.find(d => d.id === task.department);
              const taskProject = projects.find(p => p.id === task.projectId);
              const overdue = isOverdue(task.dueDate);
              const dueToday = isDueToday(task.dueDate);
              
              return (
                <tr key={task.id} onClick={() => setShowTaskModal(task)} className={`border-b hover:bg-gray-50 cursor-pointer ${overdue && task.status !== 'done' ? 'bg-red-50' : dueToday && task.status !== 'done' ? 'bg-orange-50' : ''}`}>
                  <td className="px-4 py-3 text-sm font-mono text-gray-600">{task.key}</td>
                  <td className="px-4 py-3 text-sm">{task.title}</td>
                  {selectedProject === 'all' && <td className="px-4 py-3 text-sm text-gray-600">{taskProject?.name || '—'}</td>}
                  <td className="px-4 py-3 text-sm">{taskDepartment ? <span className="text-blue-600 font-medium">{taskDepartment.name}</span> : '—'}</td>
                  <td className="px-4 py-3"><span className={`inline-flex px-2 py-1 rounded text-xs text-white ${status?.color || 'bg-gray-500'}`}>{status?.name || 'Невідомо'}</span></td>
                  <td className="px-4 py-3"><span className={`text-sm font-medium ${priority.color}`}>{priority.name}</span></td>
                  <td className="px-4 py-3 text-sm">{assignedUser?.name || '—'}</td>
                  <td className="px-4 py-3 text-sm">{task.dueDate ? <span className={overdue ? 'text-red-600 font-bold' : dueToday ? 'text-orange-600 font-bold' : ''}>{new Date(task.dueDate).toLocaleDateString('uk-UA')}</span> : '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filteredTasks.length === 0 && <div className="text-center py-8 text-gray-500">Задач не знайдено</div>}
      </div>
    );
  };

  const CompletedTasksPage = () => {
    const allCompletedTasks = tasks.filter(task => {
      const isDone = task.status === 'done' || statuses.find(s => s.id === task.status && s.name === 'Виконано');
      return isDone;
    });

    const filteredCompleted = allCompletedTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(completedSearchTerm.toLowerCase()) || task.description.toLowerCase().includes(completedSearchTerm.toLowerCase()) || task.key.toLowerCase().includes(completedSearchTerm.toLowerCase());
      const matchesAssignee = completedFilterAssignee === 'all' || task.assignee === completedFilterAssignee;
      return matchesSearch && matchesAssignee;
    });

    const sortedTasks = [...filteredCompleted].sort((a, b) => {
      if (completedSortBy === 'completedDate') return new Date(b.updatedAt) - new Date(a.updatedAt);
      if (completedSortBy === 'title') return a.title.localeCompare(b.title);
      if (completedSortBy === 'assignee') {
        const userA = users.find(u => u.id === a.assignee);
        const userB = users.find(u => u.id === b.assignee);
        return (userA?.name || '').localeCompare(userB?.name || '');
      }
      return 0;
    });

    return (
      <div>
        <div className="bg-white rounded-lg p-4 mb-6 shadow-sm">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
              <input type="text" placeholder="Пошук..." value={completedSearchTerm} onChange={(e) => setCompletedSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded" />
            </div>
            <select value={completedFilterAssignee} onChange={(e) => setCompletedFilterAssignee(e.target.value)} className="border rounded px-3 py-2">
              <option value="all">Всі виконавці</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
            </select>
            <select value={completedSortBy} onChange={(e) => setCompletedSortBy(e.target.value)} className="border rounded px-3 py-2">
              <option value="completedDate">За датою</option>
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
                  <tr key={task.id} onClick={() => setShowTaskModal(task)} className="border-b hover:bg-gray-50 cursor-pointer">
                    <td className="px-4 py-3 text-sm font-mono text-gray-600">{task.key}</td>
                    <td className="px-4 py-3 text-sm">{task.title}</td>
                    <td className="px-4 py-3 text-sm">{taskDepartment ? <span className="text-blue-600 font-medium">{taskDepartment.name}</span> : '—'}</td>
                    <td className="px-4 py-3 text-sm">{assignedUser?.name || '—'}</td>
                    <td className="px-4 py-3 text-sm">{new Date(task.updatedAt).toLocaleString('uk-UA')}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{project?.name || '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {sortedTasks.length === 0 && <div className="text-center py-8 text-gray-500">Виконаних задач не знайдено</div>}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">TaskFlow</h1>
            <div className="flex items-center gap-2">
              <button onClick={() => setActivePage('main')} className={`px-3 py-2 text-sm rounded ${activePage === 'main' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}>Активні</button>
              <button onClick={() => setActivePage('completed')} className={`px-3 py-2 text-sm rounded ${activePage === 'completed' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}>Виконані</button>
              <button onClick={() => setShowProjectManageModal(true)} className="px-3 py-2 text-sm border rounded hover:bg-gray-50">Проєкти</button>
              <button onClick={() => setShowUserManageModal(true)} className="px-3 py-2 text-sm border rounded hover:bg-gray-50">Користувачі</button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activePage === 'completed' ? (
          <CompletedTasksPage />
        ) : (
          <>
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Оберіть проєкт</label>
              <select value={selectedProject === 'all' ? 'all' : selectedProject?.id || ''} onChange={(e) => { if (e.target.value === 'all') { setSelectedProject('all'); } else { setSelectedProject(projects.find(p => p.id === e.target.value)); } }} className="w-full max-w-md border rounded px-3 py-2">
                <option value="">— Оберіть проєкт —</option>
                <option value="all">📊 Всі проєкти</option>
                {projects.map(p => <option key={p.id} value={p.id}>{p.name} ({p.key})</option>)}
              </select>
            </div>

            {(selectedProject === 'all' || selectedProject) && (
              <>
                <div className="bg-white rounded-lg p-4 mb-6 shadow-sm">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center gap-2">
                      <button onClick={() => setActiveView('board')} className={`px-4 py-2 rounded ${activeView === 'board' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}>Дошка</button>
                      <button onClick={() => setActiveView('list')} className={`px-4 py-2 rounded ${activeView === 'list' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}>Список</button>
                    </div>

                    <div className="flex items-center gap-2 flex-1 max-w-2xl">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                        <input type="text" placeholder="Пошук задач..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded" />
                      </div>
                      <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="border rounded px-3 py-2">
                        <option value="all">Всі статуси</option>
                        {(selectedProject === 'all' || !selectedProject?.customStatuses ? statuses : selectedProject.customStatuses).map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                    </div>

                    {selectedProject !== 'all' && <button onClick={() => setShowTaskModal(true)} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"><Plus size={16} className="inline mr-1" />Задачу</button>}
                  </div>
                </div>

                {activeView === 'board' ? <BoardView /> : <ListView />}
              </>
            )}

            {!selectedProject && projects.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-4">Створіть свій перший проєкт</p>
                <button onClick={() => setShowProjectModal(true)} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Створити проєкт</button>
              </div>
            )}

            {!selectedProject && projects.length > 0 && <div className="text-center py-12"><p className="text-gray-500">Оберіть проєкт</p></div>}
          </>
        )}
      </main>

      {showProjectModal && <ProjectModal onClose={() => setShowProjectModal(false)} editProject={typeof showProjectModal === 'object' ? showProjectModal : null} />}
      {showTaskModal && <TaskModal onClose={() => setShowTaskModal(false)} editTask={typeof showTaskModal === 'object' ? showTaskModal : null} />}
      {showUserModal && <UserModal onClose={() => setShowUserModal(false)} editUser={typeof showUserModal === 'object' ? showUserModal : null} />}
      {showStatusModal && <StatusModal onClose={() => setShowStatusModal(false)} editStatus={typeof showStatusModal === 'object' ? showStatusModal : null} />}
      {showProjectManageModal && <ProjectManageModal onClose={() => setShowProjectManageModal(false)} />}
      {showUserManageModal && <UserManageModal onClose={() => setShowUserManageModal(false)} />}
      {showDepartmentModal && <DepartmentModal onClose={() => setShowDepartmentModal(false)} />}
    </div>
  );
};

export default TaskManager;