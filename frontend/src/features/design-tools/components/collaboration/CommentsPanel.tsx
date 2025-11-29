/**
 * Comments Panel Component
 * Design comments and annotations
 */

import React, { useState } from "react";
import { Card } from "../../../shared/components/ui/card";
import { Button } from "../../../shared/components/ui/button";
import { Badge } from "../../../shared/components/ui/badge";
import {
  MessageSquare,
  Send,
  Edit2,
  Trash2,
  User,
  Clock,
} from "lucide-react";

interface Comment {
  id: string;
  author: string;
  content: string;
  timestamp: string;
  componentId?: string;
  resolved?: boolean;
}

interface CommentsPanelProps {
  comments: Comment[];
  onCommentAdd?: (content: string, componentId?: string) => void;
  onCommentEdit?: (id: string, content: string) => void;
  onCommentDelete?: (id: string) => void;
  onCommentResolve?: (id: string) => void;
  selectedComponentId?: string;
}

export default function CommentsPanel({
  comments,
  onCommentAdd,
  onCommentEdit,
  onCommentDelete,
  onCommentResolve,
  selectedComponentId,
}: CommentsPanelProps) {
  const [newComment, setNewComment] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");

  const filteredComments = selectedComponentId
    ? comments.filter(c => c.componentId === selectedComponentId)
    : comments;

  const handleAddComment = () => {
    if (newComment.trim()) {
      onCommentAdd?.(newComment, selectedComponentId);
      setNewComment("");
    }
  };

  const handleStartEdit = (comment: Comment) => {
    setEditingId(comment.id);
    setEditContent(comment.content);
  };

  const handleSaveEdit = () => {
    if (editingId && editContent.trim()) {
      onCommentEdit?.(editingId, editContent);
      setEditingId(null);
      setEditContent("");
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditContent("");
  };

  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">Comments</h3>
          <Badge variant="outline" className="text-xs">
            {filteredComments.length}
          </Badge>
        </div>
      </div>

      {/* Add Comment */}
      <div className="mb-4">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder={
            selectedComponentId
              ? "Add a comment about this component..."
              : "Add a general comment..."
          }
          className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-white placeholder-neutral-blue focus:outline-none focus:border-neon-teal resize-none"
          rows={3}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              handleAddComment();
            }
          }}
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-neutral-blue">
            Press Cmd/Ctrl + Enter to send
          </span>
          <Button
            size="sm"
            onClick={handleAddComment}
            disabled={!newComment.trim()}
            className="bg-neon-teal hover:bg-neon-teal/80 text-dark-bg"
          >
            <Send className="w-4 h-4 mr-1" />
            Add Comment
          </Button>
        </div>
      </div>

      {/* Comments List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {filteredComments.length === 0 ? (
          <div className="text-center py-8 text-neutral-blue">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No comments yet</p>
          </div>
        ) : (
          filteredComments.map((comment) => (
            <div
              key={comment.id}
              className={`p-3 rounded border ${
                comment.resolved
                  ? "bg-zinc-900/30 border-dark-border opacity-60"
                  : "bg-dark-bg border-dark-border"
              }`}
            >
              {editingId === comment.id ? (
                <div>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full px-2 py-1 bg-zinc-900 border border-dark-border rounded text-white text-sm resize-none"
                    rows={2}
                  />
                  <div className="flex items-center gap-2 mt-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleSaveEdit}
                      className="text-xs h-7"
                    >
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleCancelEdit}
                      className="text-xs h-7"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-neutral-blue" />
                      <span className="text-sm font-medium text-white">
                        {comment.author}
                      </span>
                      <span className="text-xs text-neutral-blue">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {new Date(comment.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      {comment.resolved && (
                        <Badge variant="outline" className="text-xs">
                          Resolved
                        </Badge>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleStartEdit(comment)}
                        className="h-6 w-6 p-0"
                      >
                        <Edit2 className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onCommentDelete?.(comment.id)}
                        className="h-6 w-6 p-0 text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-white mb-2">{comment.content}</p>
                  {!comment.resolved && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onCommentResolve?.(comment.id)}
                      className="text-xs h-7"
                    >
                      Mark as Resolved
                    </Button>
                  )}
                </>
              )}
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

