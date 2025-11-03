import { Link } from 'react-router-dom';

interface UpgradePromptProps {
  stockLimit: number;
  onDismiss?: () => void;
}

/**
 * UpgradePrompt component displayed when free tier limit is reached
 * Shows message about limit and provides upgrade button (navigation only, no payment)
 */
export default function UpgradePrompt({ stockLimit, onDismiss }: UpgradePromptProps) {
  return (
    <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-6 my-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-blue-300 mb-2">
            Free Tier Limit Reached
          </h3>
          <p className="text-blue-200 mb-4">
            You've reached your free tier limit ({stockLimit} stocks). Upgrade to premium for unlimited access to track and configure more stocks.
          </p>
          <div className="flex gap-3">
            <Link
              to="/upgrade"
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Upgrade to Premium
            </Link>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg transition-colors"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

