import React from 'react';
import { PlusCircle, CheckCircle } from 'lucide-react';

export const AddChildForm = ({ newChild, setNewChild, onSubmit }) => (
  <form onSubmit={onSubmit} className="mb-4">
    <div className="flex gap-2">
      <input
        type="text"
        placeholder="Name"
        className="flex-1 p-2 border rounded"
        value={newChild.name}
        onChange={(e) => setNewChild({ ...newChild, name: e.target.value })}
      />
      <input
        type="number"
        placeholder="Allowance"
        className="w-24 p-2 border rounded"
        value={newChild.weekly_allowance}
        onChange={(e) => setNewChild({ ...newChild, weekly_allowance: parseFloat(e.target.value) })}
      />
      <button type="submit" className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600">
        <PlusCircle className="h-5 w-5" />
      </button>
    </div>
  </form>
);

export const ChildList = ({ 
  children, 
  assignments, 
  chores,
  selectedChores,
  setSelectedChores,
  onAssignChores,
  onCompleteChore
}) => (
  <div className="space-y-2">
    {children.map(child => (
      <div key={child.id} className="p-3 border rounded">
        <div className="flex justify-between items-center">
          <span className="font-medium">{child.name}</span>
          <span className="text-green-600">${child.weekly_allowance}</span>
        </div>

        <div className="mt-2">
          <select
            multiple
            className="w-full p-2 border rounded mt-2"
            value={selectedChores[child.id] || []}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => parseInt(option.value));
              setSelectedChores({
                ...selectedChores,
                [child.id]: selected
              });
            }}
          >
            {chores.map(chore => (
              <option key={chore.id} value={chore.id}>
                {chore.name} ({chore.points} pts)
              </option>
            ))}
          </select>
          <button
            onClick={() => onAssignChores(child.id)}
            className="w-full mt-2 p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Assign Selected Chores
          </button>
        </div>

        <div className="mt-2 space-y-1">
          {assignments[child.id]?.map(assignment => (
            <div key={assignment.id} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded">
              <div className="flex items-center space-x-2">
                <span className="font-medium">{assignment.chore.name}</span>
                <span className="text-gray-600">({assignment.chore.points} pts)</span>
              </div>
              {assignment.is_completed ? (
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-gray-500">
                    {new Date(assignment.completion_date).toLocaleDateString()}
                  </span>
                </div>
              ) : (
                <button
                  onClick={() => onCompleteChore(assignment.id)}
                  className="text-blue-500 hover:text-blue-600"
                >
                  Complete
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);