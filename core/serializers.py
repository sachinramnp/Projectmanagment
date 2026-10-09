from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project,ProjectMembership,Board,BoardColumn,Task,Comment,Profile
class UserBrief(serializers.ModelSerializer):
    full_name=serializers.CharField(source="profile.full_name",read_only=True)
    class Meta: model=User; fields=["id","username","email","full_name"]
class ProfileSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(source="user.email")
    class Meta: model=Profile; fields=["full_name","role","email"]
class ProjectSerializer(serializers.ModelSerializer):
    owner=UserBrief(read_only=True)
    member_ids=serializers.PrimaryKeyRelatedField(source="members",many=True,queryset=User.objects.all(),required=False)
    class Meta: model=Project; fields=["id","name","description","owner","status","priority","start_date","due_date","created_at","updated_at","is_archived","member_ids"]
    def create(self,validated_data):
        members=validated_data.pop("members",[])
        p=Project.objects.create(owner=self.context["request"].user,**validated_data)
        p.members.add(self.context["request"].user,*members)
        return p
class ColumnSerializer(serializers.ModelSerializer):
    class Meta: model=BoardColumn; fields=["id","board","name","position"]; read_only_fields=["board"]
class CommentSerializer(serializers.ModelSerializer):
    user=UserBrief(read_only=True)
    class Meta: model=Comment; fields=["id","task","user","content","created_at","updated_at"]; read_only_fields=["user","created_at","updated_at"]
class TaskSerializer(serializers.ModelSerializer):
    created_by=UserBrief(read_only=True)
    class Meta: model=Task; fields=["id","project","column","title","description","assigned_to","created_by","priority","status","start_date","due_date","position","created_at","updated_at","completed_at"]; read_only_fields=["created_by","created_at","updated_at","completed_at"]
    def validate(self,attrs):
        project=attrs.get("project",getattr(self.instance,"project",None))
        column=attrs.get("column",getattr(self.instance,"column",None))
        if column and project and column.board.project_id!=project.id: raise serializers.ValidationError("Column must belong to the selected project.")
        return attrs
