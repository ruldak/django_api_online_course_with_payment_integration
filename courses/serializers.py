from rest_framework import serializers
from .models import Course, Lesson, Category, Cart, CartItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order']

class CreateCourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, write_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'category', 'price', 'created_at', 'lessons']

    def create(self, validated_data):
        lessons_data = validated_data.pop('lessons', [])
        course = Course.objects.create(**validated_data)

        lessons = []

        for data in lessons_data:
            lessons.append(Lesson(course=course, **data))

        Lesson.objects.bulk_create(lessons)

        return course

class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.username', read_only=True)
    category_name = serializers.CharField(source='category', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'description', 'category', 'category_name', 'instructor_name', 'price', 'created_at')

class CartItemSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.title', read_only=True)
    course_price = serializers.DecimalField(
        source='course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'course',
            'status',
            'course_name',
            'course_price',
        ]
        read_only_fields = ['id']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name="get_total_price")
    user_detail = serializers.CharField(source='user', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user_detail', 'items', 'total_price', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return obj.get_total_price()
