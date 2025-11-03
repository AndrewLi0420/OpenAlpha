import { useAuth } from '../hooks/useAuth';

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
        <h2 className="text-xl font-semibold mb-4">Welcome!</h2>
        {user && (
          <div className="space-y-2 text-gray-300">
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>Tier:</strong> {user.tier}
            </p>
            <p>
              <strong>Verified:</strong> {user.is_verified ? 'Yes' : 'No'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

